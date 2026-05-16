import json
from pathlib import Path

import pytest

from podcast_auto_editor.alignment import (
    SCHEMA_VERSION,
    AlignmentError,
    AlignmentProviderError,
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


def test_whisperx_via_align_to_file_surfaces_error_without_writing(tmp_path):
    out = tmp_path / "out.json"
    with pytest.raises(AlignmentProviderError):
        align_to_file("audio.wav", [], out, provider="whisperx")
    assert not out.exists()
