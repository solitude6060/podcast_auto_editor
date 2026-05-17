import json
from pathlib import Path

import pytest

from podcast_auto_editor.diarization import (
    SCHEMA_VERSION,
    DiarizationError,
    DiarizationProviderError,
    MockDiarizationProvider,
    PyannoteDiarizationProvider,
    diarize_to_file,
    normalize_speaker_segments,
)


def _write_config(tmp_path: Path) -> tuple[Path, Path]:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt fake-audio")
    config_path = tmp_path / "diar.json"
    config_path.write_text(json.dumps({
        "segments": [
            {"start": 0.0, "end": 5.0, "speaker_id": "spk0", "confidence": 0.95},
            {"start": 5.0, "end": 10.0, "speaker_id": "spk1", "confidence": 0.92},
        ]
    }))
    return audio, config_path


def test_mock_diarization_returns_configured_segments(tmp_path):
    audio, config_path = _write_config(tmp_path)

    provider = MockDiarizationProvider(config_path=config_path)
    segments = provider.diarize(audio)

    assert len(segments) == 2
    assert segments[0]["start"] == 0.0
    assert segments[0]["end"] == 5.0
    assert segments[0]["speaker_id"] == "spk0"
    assert segments[0]["confidence"] == 0.95
    assert segments[1]["speaker_id"] == "spk1"


def test_mock_diarization_returns_empty_list_without_config(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    provider = MockDiarizationProvider()
    assert provider.diarize(audio) == []


def test_normalize_speaker_segments_validates_required_fields():
    valid = normalize_speaker_segments([
        {"start": 0.0, "end": 1.0, "speaker_id": "spk0", "confidence": 0.8}
    ])
    assert valid[0]["speaker_id"] == "spk0"

    with pytest.raises(DiarizationError, match="speaker_id"):
        normalize_speaker_segments([{"start": 0.0, "end": 1.0, "confidence": 0.8}])

    with pytest.raises(DiarizationError, match="start"):
        normalize_speaker_segments([{"end": 1.0, "speaker_id": "spk0", "confidence": 0.8}])

    with pytest.raises(DiarizationError, match="end"):
        normalize_speaker_segments([{"start": 1.0, "end": 0.5, "speaker_id": "spk0", "confidence": 0.8}])


def test_normalize_speaker_segments_rejects_negative_start():
    """Triple-review (Gemini LOW + MiniMax CRITICAL + Codex MEDIUM):
    start < 0 must be rejected, mirroring transcript.py:59."""
    with pytest.raises(DiarizationError, match="start"):
        normalize_speaker_segments([{"start": -0.5, "end": 1.0, "speaker_id": "spk0"}])


def test_normalize_speaker_segments_rejects_non_finite_timestamps():
    """Triple-review (Codex MEDIUM): NaN / inf must not slip through `float(value)`."""
    nan = float("nan")
    inf = float("inf")
    with pytest.raises(DiarizationError):
        normalize_speaker_segments([{"start": nan, "end": 1.0, "speaker_id": "spk0"}])
    with pytest.raises(DiarizationError):
        normalize_speaker_segments([{"start": 0.0, "end": inf, "speaker_id": "spk0"}])


def test_normalize_speaker_segments_rejects_boolean_timestamps():
    """Triple-review (Codex MEDIUM): bool is a subtype of int; the validator
    must reject it explicitly so `True` (=1.0) and `False` (=0.0) do not
    silently map to seconds."""
    with pytest.raises(DiarizationError):
        normalize_speaker_segments([{"start": True, "end": 1.0, "speaker_id": "spk0"}])
    with pytest.raises(DiarizationError):
        normalize_speaker_segments([{"start": 0.0, "end": False, "speaker_id": "spk0"}])


def test_normalize_speaker_segments_clamps_confidence():
    out = normalize_speaker_segments([
        {"start": 0.0, "end": 1.0, "speaker_id": "spk0", "confidence": 1.5},
        {"start": 1.0, "end": 2.0, "speaker_id": "spk1", "confidence": -0.2},
    ])
    assert out[0]["confidence"] == 1.0
    assert out[1]["confidence"] == 0.0


def test_diarize_to_file_writes_canonical_schema(tmp_path):
    audio, config_path = _write_config(tmp_path)
    out = tmp_path / "speaker_segments.v1.json"

    result = diarize_to_file(audio, out, provider="mock", config_path=config_path)

    assert result == out
    data = json.loads(out.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert len(data["segments"]) == 2
    assert data["segments"][0]["speaker_id"] == "spk0"


def test_diarize_to_file_writes_empty_segments_artefact(tmp_path):
    """Triple-review (MiniMax MEDIUM): the empty-segments path through
    `diarize_to_file` (no --config given) must produce a valid artefact
    with `segments: []`, not an error or a missing file."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    out = tmp_path / "out.json"

    result = diarize_to_file(audio, out, provider="mock")

    assert result == out
    data = json.loads(out.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["segments"] == []


def test_mock_provider_wraps_invalid_json_as_diarization_error(tmp_path):
    """Triple-review (Gemini MEDIUM): malformed mock config JSON must
    surface as a clean DiarizationError so the CLI handler can convert
    it to a non-zero exit, not bubble up as a JSONDecodeError traceback."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    config = tmp_path / "bad.json"
    config.write_text("{not valid json")

    provider = MockDiarizationProvider(config_path=config)
    with pytest.raises(DiarizationError):
        provider.diarize(audio)


def test_mock_provider_wraps_missing_config_as_diarization_error(tmp_path):
    """Triple-review (Gemini MEDIUM): a missing config file must surface as
    a DiarizationError, not a raw FileNotFoundError."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    missing = tmp_path / "does-not-exist.json"

    provider = MockDiarizationProvider(config_path=missing)
    with pytest.raises(DiarizationError):
        provider.diarize(audio)


def test_diarize_to_file_rejects_unknown_provider(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    out = tmp_path / "out.json"
    with pytest.raises(DiarizationError, match="unknown provider"):
        diarize_to_file(audio, out, provider="not-a-real-provider")


def test_pyannote_provider_raises_clear_error_when_called(tmp_path):
    """Until PR-C2 lands real pyannote integration, calling the adapter
    must raise a clear DiarizationProviderError so users know how to
    proceed. The message mentions either the missing dependency
    (`pyannote-audio`) or the deferred follow-up integration."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    provider = PyannoteDiarizationProvider()
    with pytest.raises(DiarizationProviderError) as exc_info:
        provider.diarize(audio)
    msg = str(exc_info.value).lower()
    assert "pyannote" in msg or "deferred" in msg, msg


def test_pyannote_provider_via_diarize_to_file_raises_clear_error(tmp_path):
    """End-to-end: CLI-equivalent flow via diarize_to_file must surface the
    pyannote provider error, not silently write an empty artefact."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    out = tmp_path / "out.json"
    with pytest.raises(DiarizationProviderError):
        diarize_to_file(audio, out, provider="pyannote")
    assert not out.exists()
