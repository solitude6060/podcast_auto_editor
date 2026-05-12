import json
import tempfile
from pathlib import Path

from podcast_auto_editor.config import load_config


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
