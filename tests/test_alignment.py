import json
from pathlib import Path

import pytest

from podcast_auto_editor.alignment import (
    SCHEMA_VERSION,
    AlignmentError,
    AlignmentProviderError,
    LattifaiAlignmentProvider,
    MockAlignmentProvider,
    WhisperXAlignmentProvider,
    align_to_file,
    normalize_word_alignments,
)


def test_mock_alignment_from_config(tmp_path):
    config = tmp_path / "align.json"
    config.write_text(json.dumps({
        "words": [
            {"start": 0.0, "end": 0.5, "text": "你好"},
            {"start": 0.5, "end": 1.0, "text": "歡迎"},
        ]
    }))

    provider = MockAlignmentProvider(config_path=config)
    words = provider.align("audio.wav", [])

    assert len(words) == 2
    assert words[0]["text"] == "你好"


def test_mock_alignment_synthesizes_from_transcript_when_no_config():
    provider = MockAlignmentProvider()
    words = provider.align(
        "audio.wav",
        [
            {"start": 0.0, "end": 2.0, "text": "hello world from CI"},
        ],
    )
    # 4 whitespace tokens → 4 evenly-spaced 0.5s words
    assert len(words) == 4
    assert words[0]["text"] == "hello"
    assert words[1]["text"] == "world"
    assert words[0]["start"] == 0.0
    assert pytest.approx(words[1]["start"]) == 0.5


def test_mock_alignment_synthesizes_cjk_per_character():
    provider = MockAlignmentProvider()
    words = provider.align(
        "audio.wav",
        [{"start": 0.0, "end": 2.0, "text": "你好世界"}],
    )
    # No whitespace → one word per character → 4 words
    assert len(words) == 4
    assert [w["text"] for w in words] == ["你", "好", "世", "界"]


def test_mock_alignment_synthesizes_mixed_cjk_and_ascii():
    """Triple-review HIGH: 'hello 世界' must produce 3 tokens
    (ASCII word stays a unit, CJK chars split). Pre-fix it produced 2
    coarse tokens because `text.split()` treated 世界 as one word."""
    provider = MockAlignmentProvider()
    words = provider.align(
        "audio.wav",
        [{"start": 0.0, "end": 3.0, "text": "hello 世界"}],
    )
    assert [w["text"] for w in words] == ["hello", "世", "界"]


def test_mock_alignment_handles_newline_only_text():
    """Triple-review MEDIUM (Gemini): 'hello\\nworld' has no space but does
    have whitespace. Pre-fix the `' ' in text` check fell through to
    list(text), char-splitting 11 chars including the newline. Fix uses
    text.split() which handles ALL whitespace."""
    provider = MockAlignmentProvider()
    words = provider.align(
        "audio.wav",
        [{"start": 0.0, "end": 2.0, "text": "hello\nworld"}],
    )
    assert [w["text"] for w in words] == ["hello", "world"]


def test_mock_alignment_skips_empty_text_and_zero_duration_segments():
    """Triple-review MEDIUM (Codex): silently skipping these is the
    documented design; pin the contract so a future refactor doesn't
    accidentally start raising."""
    provider = MockAlignmentProvider()
    words = provider.align(
        "audio.wav",
        [
            {"start": 0.0, "end": 1.0, "text": ""},          # empty → skip
            {"start": 1.0, "end": 1.0, "text": "x"},         # zero duration → skip
            {"start": 2.0, "end": 1.5, "text": "y"},         # negative duration → skip
            {"start": 3.0, "end": 4.0, "text": "real"},      # kept
        ],
    )
    assert [w["text"] for w in words] == ["real"]


def test_align_to_file_writes_empty_segments_artefact(tmp_path):
    """Triple-review HIGH (MiniMax + Codex): empty transcript_segments
    through align_to_file produces a valid artefact with `words: []`,
    same intentional behaviour the diarization test pins."""
    out = tmp_path / "out.json"
    result = align_to_file("audio.wav", [], out, provider="mock")
    assert result == out
    data = json.loads(out.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["audio_path"] == "audio.wav"
    assert data["words"] == []


def test_normalize_word_alignments_validates_required_fields():
    with pytest.raises(AlignmentError, match="text"):
        normalize_word_alignments([{"start": 0.0, "end": 1.0}])
    with pytest.raises(AlignmentError, match="start"):
        normalize_word_alignments([{"end": 1.0, "text": "x"}])
    with pytest.raises(AlignmentError, match="end"):
        normalize_word_alignments([{"start": 1.0, "end": 0.5, "text": "x"}])


def test_normalize_word_alignments_rejects_non_finite_and_bool():
    with pytest.raises(AlignmentError):
        normalize_word_alignments([{"start": float("nan"), "end": 1.0, "text": "x"}])
    with pytest.raises(AlignmentError):
        normalize_word_alignments([{"start": True, "end": 1.0, "text": "x"}])
    with pytest.raises(AlignmentError):
        normalize_word_alignments([{"start": -0.5, "end": 1.0, "text": "x"}])


def test_align_to_file_writes_canonical_schema(tmp_path):
    out = tmp_path / "word_alignments.v1.json"

    result = align_to_file(
        "audio.wav",
        [{"start": 0.0, "end": 2.0, "text": "hello world"}],
        out,
        provider="mock",
    )

    assert result == out
    data = json.loads(out.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["audio_path"] == "audio.wav"
    assert len(data["words"]) == 2


def test_align_to_file_rejects_unknown_provider(tmp_path):
    with pytest.raises(AlignmentError, match="unknown provider"):
        align_to_file("audio.wav", [], tmp_path / "out.json", provider="not-a-provider")


def test_whisperx_provider_raises_clear_error_when_called(tmp_path):
    """Until PR-X3.1 lands real WhisperX integration, calling the adapter
    must raise a clear AlignmentProviderError so users know how to proceed."""
    provider = WhisperXAlignmentProvider()
    with pytest.raises(AlignmentProviderError) as exc_info:
        provider.align("audio.wav", [{"start": 0.0, "end": 1.0, "text": "x"}])
    msg = str(exc_info.value).lower()
    assert "whisperx" in msg or "deferred" in msg
    # Triple-review MEDIUM (MiniMax F9): error must be AlignmentProviderError,
    # not raw ImportError leaking through to the caller.
    assert isinstance(exc_info.value, AlignmentProviderError)
    assert not isinstance(exc_info.value, ImportError)


def test_whisperx_via_align_to_file_surfaces_error_without_writing(tmp_path):
    out = tmp_path / "out.json"
    with pytest.raises(AlignmentProviderError):
        align_to_file("audio.wav", [], out, provider="whisperx")
    assert not out.exists()


def test_lattifai_provider_raises_clear_error_when_called(tmp_path, monkeypatch):
    """PR-X4.1: Lattifai adapter raises a clear AlignmentProviderError when
    no model_path is provided and PAE_LATTIFAI_ONNX_PATH is unset."""
    monkeypatch.delenv("PAE_LATTIFAI_ONNX_PATH", raising=False)
    provider = LattifaiAlignmentProvider()
    with pytest.raises(AlignmentProviderError) as exc_info:
        provider.align("audio.wav", [{"start": 0.0, "end": 1.0, "text": "x"}])
    msg = str(exc_info.value)
    # PR-X4.1: message must mention both configuration options (no longer says "deferred")
    assert "model_path" in msg
    assert "PAE_LATTIFAI_ONNX_PATH" in msg
    # Triple-review MEDIUM (MiniMax F9): class-level assertion
    assert isinstance(exc_info.value, AlignmentProviderError)
    assert not isinstance(exc_info.value, ImportError)


def test_lattifai_via_align_to_file_surfaces_error_without_writing(tmp_path):
    out = tmp_path / "out.json"
    with pytest.raises(AlignmentProviderError):
        align_to_file("audio.wav", [], out, provider="lattifai")
    assert not out.exists()


def test_align_to_file_rejects_unknown_provider_after_lattifai_added(tmp_path):
    """Regression guard for PR-X4: the error message lists all three known
    providers after lattifai is registered."""
    try:
        align_to_file("audio.wav", [], tmp_path / "out.json", provider="not-a-provider")
    except AlignmentError as exc:
        assert "mock" in str(exc)
        assert "whisperx" in str(exc)
        assert "lattifai" in str(exc)
    else:
        raise AssertionError("expected AlignmentError for unknown provider")
