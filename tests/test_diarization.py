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
