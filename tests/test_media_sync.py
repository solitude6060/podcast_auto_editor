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


def test_render_audio_uses_two_pass_loudnorm(monkeypatch, tmp_path):
    calls = []

    def fake_run_command(command, **kwargs):
        calls.append(command)
        if "-f" in command and "null" in command:
            return type("Result", (), {
                "returncode": 0,
                "stderr": """
                {
                  "input_i": "-17.30",
                  "input_tp": "-3.60",
                  "input_lra": "9.40",
                  "input_thresh": "-28.50",
                  "target_offset": "1.30"
                }
                """,
            })()
        return type("Result", (), {"returncode": 0, "stderr": ""})()

    monkeypatch.setattr(media, "require_tool", lambda name: None)
    monkeypatch.setattr(media, "run_command", fake_run_command)

    media.render_audio(
        "input.wav",
        tmp_path / "episode.podcast-stereo.mp3",
        [{"source_start": 0.0, "source_end": 10.0}],
        load_config(),
        channels=2,
    )

    assert len(calls) == 2
    assert "print_format=json" in calls[0][calls[0].index("-af") + 1]
    second_filter = calls[1][calls[1].index("-af") + 1]
    assert second_filter.index("aformat=channel_layouts=stereo") < second_filter.index("loudnorm=")
    assert "measured_I=-17.30" in second_filter
    assert "measured_TP=-3.60" in second_filter
    assert "measured_LRA=9.40" in second_filter
    assert "measured_thresh=-28.50" in second_filter
    assert "offset=1.30" in second_filter


def test_render_audio_converts_to_mono_before_loudnorm(monkeypatch, tmp_path):
    calls = []

    def fake_run_command(command, **kwargs):
        calls.append(command)
        if "-f" in command and "null" in command:
            return type("Result", (), {
                "returncode": 0,
                "stderr": '{"input_i":"-19.0","input_tp":"-4.0","input_lra":"8.0","input_thresh":"-30.0","target_offset":"0.0"}',
            })()
        return type("Result", (), {"returncode": 0, "stderr": ""})()

    monkeypatch.setattr(media, "require_tool", lambda name: None)
    monkeypatch.setattr(media, "run_command", fake_run_command)

    media.render_audio(
        "input.wav",
        tmp_path / "episode.podcast-mono.mp3",
        [{"source_start": 0.0, "source_end": 10.0}],
        load_config(),
        channels=1,
    )

    analysis_filter = calls[0][calls[0].index("-af") + 1]
    render_filter = calls[1][calls[1].index("-af") + 1]
    assert analysis_filter.index("aformat=channel_layouts=mono") < analysis_filter.index("loudnorm=")
    assert render_filter.index("aformat=channel_layouts=mono") < render_filter.index("loudnorm=")


def test_render_audio_uses_lossy_true_peak_margin_for_mp3(monkeypatch, tmp_path):
    calls = []

    def fake_run_command(command, **kwargs):
        calls.append(command)
        if "-f" in command and "null" in command:
            return type("Result", (), {
                "returncode": 0,
                "stderr": '{"input_i":"-16.0","input_tp":"-4.0","input_lra":"8.0","input_thresh":"-30.0","target_offset":"0.0"}',
            })()
        return type("Result", (), {"returncode": 0, "stderr": ""})()

    monkeypatch.setattr(media, "require_tool", lambda name: None)
    monkeypatch.setattr(media, "run_command", fake_run_command)

    media.render_audio(
        "input.wav",
        tmp_path / "episode.podcast-stereo.mp3",
        [{"source_start": 0.0, "source_end": 10.0}],
        load_config(),
        channels=2,
    )

    assert "TP=-2.0" in calls[0][calls[0].index("-af") + 1]
    assert "TP=-2.0" in calls[1][calls[1].index("-af") + 1]
