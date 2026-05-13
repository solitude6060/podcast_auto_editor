import pytest

from podcast_auto_editor.artifacts import run_paths
from podcast_auto_editor.config import load_config
from podcast_auto_editor.exports import EXPORT_PROFILES, export_output_path
from podcast_auto_editor.media import MediaToolError
from podcast_auto_editor.pipeline import render
from podcast_auto_editor.timeline import create_noop_timeline


def test_builtin_export_profiles_have_stable_outputs(tmp_path):
    paths = run_paths(tmp_path, "ep1")

    assert set(EXPORT_PROFILES) == {"archive-wav", "podcast-stereo", "podcast-mono"}
    assert export_output_path(paths, EXPORT_PROFILES["archive-wav"]) == paths.edited_wav
    assert export_output_path(paths, EXPORT_PROFILES["podcast-stereo"]).name == "episode.podcast-stereo.mp3"
    assert export_output_path(paths, EXPORT_PROFILES["podcast-mono"]).name == "episode.podcast-mono.mp3"


def test_render_records_per_profile_quality_reports(monkeypatch, tmp_path):
    from podcast_auto_editor import pipeline

    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 2}])
    paths = run_paths(tmp_path, "ep1")
    calls = []

    def fake_render_audio(input_path, output_path, kept, config, channels=2):
        calls.append((output_path.name, channels))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")

    def fake_measure_audio_quality(path):
        if path.name == "episode.podcast-mono.mp3":
            return {"integrated_lufs": -19.0, "true_peak_db": -2.0, "clipped_samples": 0}
        return {"integrated_lufs": -16.0, "true_peak_db": -2.0, "clipped_samples": 0}

    monkeypatch.setattr(pipeline, "render_audio", fake_render_audio)
    monkeypatch.setattr(pipeline, "measure_audio_quality", fake_measure_audio_quality)

    rendered = render("input.wav", paths, timeline, load_config())

    assert calls == [
        ("episode.edited.wav", 2),
        ("episode.podcast-stereo.mp3", 2),
        ("episode.podcast-mono.mp3", 1),
    ]
    profiles = rendered["export_metadata"]["export_profiles"]
    assert [profile["name"] for profile in profiles] == ["archive-wav", "podcast-stereo", "podcast-mono"]
    assert all(profile["quality_gate_report"]["passed"] for profile in profiles)
    assert rendered["export_metadata"]["edited_audio"] == str(paths.edited_wav)
    assert rendered["export_metadata"]["quality_gate_report"] == profiles[0]["quality_gate_report"]


def test_render_quality_failure_names_profile(monkeypatch, tmp_path):
    from podcast_auto_editor import pipeline

    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 2}])
    paths = run_paths(tmp_path, "ep1")

    def fake_render_audio(input_path, output_path, kept, config, channels=2):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")

    def fake_measure_audio_quality(path):
        if path.name == "episode.podcast-stereo.mp3":
            return {"integrated_lufs": -30.0, "true_peak_db": -2.0, "clipped_samples": 0}
        return {"integrated_lufs": -16.0, "true_peak_db": -2.0, "clipped_samples": 0}

    monkeypatch.setattr(pipeline, "render_audio", fake_render_audio)
    monkeypatch.setattr(pipeline, "measure_audio_quality", fake_measure_audio_quality)

    with pytest.raises(MediaToolError, match="quality gate failed for podcast-stereo: loudness"):
        render("input.wav", paths, timeline, load_config())


def test_render_honors_selected_export_profiles(monkeypatch, tmp_path):
    from podcast_auto_editor import pipeline

    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 2}])
    paths = run_paths(tmp_path, "ep1")
    calls = []

    def fake_render_audio(input_path, output_path, kept, config, channels=2):
        calls.append((output_path.name, channels))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")

    monkeypatch.setattr(pipeline, "render_audio", fake_render_audio)
    monkeypatch.setattr(pipeline, "measure_audio_quality", lambda path: {"integrated_lufs": -19.0, "true_peak_db": -2.0, "clipped_samples": 0})

    rendered = render("input.wav", paths, timeline, load_config(), export_profile_names=["podcast-mono"])

    assert calls == [("episode.podcast-mono.mp3", 1)]
    assert [profile["name"] for profile in rendered["export_metadata"]["export_profiles"]] == ["podcast-mono"]
    assert rendered["export_metadata"]["edited_audio"] == str(paths.exports / "episode.podcast-mono.mp3")
    assert rendered["export_metadata"]["quality_gate_report"] == rendered["export_metadata"]["export_profiles"][0]["quality_gate_report"]


def test_render_rejects_unknown_export_profile(tmp_path):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 2}])
    paths = run_paths(tmp_path, "ep1")

    with pytest.raises(ValueError, match="unknown export profile: video-social"):
        render("input.wav", paths, timeline, load_config(), export_profile_names=["video-social"])
