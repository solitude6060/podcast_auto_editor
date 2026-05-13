from podcast_auto_editor import media
from podcast_auto_editor.config import load_config
from podcast_auto_editor.media import validate_source_av_sync


def test_av_sync_fails_when_stream_durations_unmeasured(monkeypatch):
    def fake_probe(path):
        return {"duration": 10.0}, [
            {"type": "audio"},
            {"type": "video"},
        ]
    monkeypatch.setattr(media, "probe_media", fake_probe)
    report = media.measure_av_sync("dummy.mp4")
    assert report["passed"] is False
    assert report["drift_s"] is None
    assert "unmeasured" in report["reason"]


def test_av_sync_uses_measured_stream_duration(monkeypatch):
    def fake_probe(path):
        return {"duration": 10.0}, [
            {"type": "audio", "duration": 10.00},
            {"type": "video", "duration": 10.05},
        ]
    monkeypatch.setattr(media, "probe_media", fake_probe)
    report = media.measure_av_sync("dummy.mp4")
    assert report["passed"] is True
    assert round(report["drift_s"], 3) == 0.05
    assert report["audio_duration_s"] == 10.00
    assert report["video_duration_s"] == 10.05


def test_probe_media_preserves_missing_stream_duration(monkeypatch):
    def fake_ffprobe(path):
        return {
            "format": {"duration": "10.0", "format_name": "mov,mp4", "size": "123"},
            "streams": [
                {"index": 0, "codec_type": "video", "codec_name": "h264", "time_base": "1/90000", "start_pts": 0},
                {"index": 1, "codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 2},
            ],
        }
    monkeypatch.setattr(media, "ffprobe", fake_ffprobe)
    monkeypatch.setattr(media, "sha256_file", lambda path: "hash")
    manifest, tracks = media.probe_media("dummy.mp4")
    assert manifest["duration"] == 10.0
    assert all("duration" not in track or track["duration"] is None for track in tracks)
    report = media.measure_av_sync("dummy.mp4")
    assert report["passed"] is False
    assert report["reason"] == "unmeasured stream duration"


def test_source_av_sync_validation_fails_missing_or_drifting_streams():
    cfg = load_config()
    missing = validate_source_av_sync([
        {"type": "audio", "duration": None},
        {"type": "video", "duration": 10.0},
    ], cfg.quality)
    assert missing["passed"] is False
    assert missing["reason"] == "unmeasured source stream duration"

    drifting = validate_source_av_sync([
        {"type": "audio", "duration": 10.0},
        {"type": "video", "duration": 10.5},
    ], cfg.quality)
    assert drifting["passed"] is False
    assert drifting["drift_s"] == 0.5
