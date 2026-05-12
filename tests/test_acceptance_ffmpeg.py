import json
import shutil
import subprocess
from pathlib import Path

import pytest

from podcast_auto_editor.config import load_config
from podcast_auto_editor.pipeline import run_pipeline

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg/ffprobe required")


def run_ffmpeg(args):
    result = subprocess.run(["ffmpeg", "-y", "-hide_banner", *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0, result.stderr


def make_silence_fixture(path: Path):
    run_ffmpeg([
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono:d=2",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
        "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1",
        str(path),
    ])


def make_mp4_fixture(path: Path):
    run_ffmpeg([
        "-f", "lavfi", "-i", "testsrc=size=64x64:rate=25:duration=1",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-shortest", "-pix_fmt", "yuv420p", str(path),
    ])


def test_full_audio_run_creates_real_artifacts_and_quality_report(tmp_path):
    input_path = tmp_path / "input.wav"
    make_silence_fixture(input_path)
    paths = run_pipeline(input_path, tmp_path / "runs", load_config(), episode_id="audioep")

    accepted = json.loads(paths.accepted_timeline.read_text())
    proposed = json.loads(paths.proposed_timeline.read_text())
    assert paths.before_after_preview.exists() and paths.before_after_preview.stat().st_size > 0
    assert paths.edited_wav.exists() and paths.edited_wav.stat().st_size > 0
    assert paths.recovery_map.exists()
    assert paths.subtitles_srt.exists() and paths.subtitles_vtt.exists() and paths.chapters.exists()
    assert any(op["type"] == "silence_cut" for op in proposed["operations"])
    assert all(op["type"] != "retake_cut" or op["state"] == "proposed" for op in accepted["operations"])
    gate = accepted["export_metadata"]["quality_gate_report"]
    assert gate["passed"] is True
    assert {check["name"] for check in gate["checks"]} >= {"loudness", "true_peak", "clipped_samples"}


def test_retake_candidates_are_not_bulk_accepted_in_full_run(tmp_path):
    input_path = tmp_path / "input.wav"
    make_silence_fixture(input_path)
    transcript = [
        {"start": 0.1, "end": 0.5, "text": "bad take"},
        {"start": 0.6, "end": 0.9, "text": "let me say that again"},
    ]
    paths = run_pipeline(input_path, tmp_path / "runs", load_config(), episode_id="retakeep", transcript_segments=transcript)
    accepted = json.loads(paths.accepted_timeline.read_text())
    retakes = [op for op in accepted["operations"] if op["type"] == "retake_cut"]
    assert retakes
    assert all(op["state"] == "proposed" for op in retakes)


def test_mp4_run_records_sync_gate(tmp_path):
    input_path = tmp_path / "input.mp4"
    make_mp4_fixture(input_path)
    paths = run_pipeline(input_path, tmp_path / "runs", load_config(), episode_id="mp4ep")
    accepted = json.loads(paths.accepted_timeline.read_text())
    assert paths.edited_mp4.exists() and paths.edited_mp4.stat().st_size > 0
    checks = {check["name"]: check for check in accepted["export_metadata"]["quality_gate_report"]["checks"]}
    assert checks["av_sync"]["passed"] is True
    assert checks["av_sync"]["actual"] <= 0.100
