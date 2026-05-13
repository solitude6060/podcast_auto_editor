import json
import tempfile
from pathlib import Path

import pytest

from podcast_auto_editor.config import ConfigValidationError, load_config, validate_config


def test_default_config_matches_quality_gate_contract():
    cfg = load_config()
    q = cfg.quality
    assert q.stereo_loudness_lufs == -16.0
    assert q.mono_loudness_lufs == -19.0
    assert q.loudness_tolerance_lu == 1.0
    assert q.true_peak_ceiling_db == -1.0
    assert q.silence_threshold_dbfs == -40.0
    assert q.min_silence_duration_s == 1.5
    assert q.speech_padding_s == 0.25
    assert q.max_clipped_samples == 0
    assert q.av_sync_tolerance_s == 0.100
    assert q.subtitle_tolerance_s == 0.250


def test_config_overrides_merge_with_defaults():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "config.json"
        path.write_text(json.dumps({"quality": {"min_silence_duration_s": 2.0}, "retake": {"auto_low_risk_speech": True}}))
        cfg = load_config(path)
    assert cfg.quality.min_silence_duration_s == 2.0
    assert cfg.quality.stereo_loudness_lufs == -16.0
    assert cfg.retake.auto_low_risk_speech is True


def test_config_validation_rejects_invalid_quality_and_format_values():
    with pytest.raises(ConfigValidationError) as exc:
        validate_config(load_config_dict({"quality": {"min_silence_duration_s": 0, "speech_padding_s": -0.1}, "output_audio_ext": "flac"}))

    message = str(exc.value)
    assert "min_silence_duration_s must be > 0" in message
    assert "speech_padding_s must be >= 0" in message
    assert "output_audio_ext must be one of" in message


def test_load_config_fails_fast_on_invalid_values(tmp_path):
    path = tmp_path / "bad-config.json"
    path.write_text(json.dumps({"retake": {"auto_accept_confidence": 1.5}}))

    with pytest.raises(ConfigValidationError, match="auto_accept_confidence must be between 0 and 1"):
        load_config(path)


def load_config_dict(data):
    path = Path(tempfile.mkdtemp()) / "config.json"
    path.write_text(json.dumps(data))
    return load_config(path)


def test_config_accepts_export_profile_subset(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"export_profiles": ["archive-wav", "podcast-mono"]}')

    config = load_config(path)

    assert config.export_profiles == ("archive-wav", "podcast-mono")


def test_config_rejects_unknown_export_profile(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"export_profiles": ["video-social"]}')

    try:
        load_config(path)
    except Exception as exc:
        assert "unknown export profile: video-social" in str(exc)
    else:
        raise AssertionError("expected invalid export profile to fail")
