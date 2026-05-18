import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import podcast_auto_editor.cli as cli
from podcast_auto_editor.fixtures import make_silence_fixture


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _make_spiky_wav(path: Path) -> Path:
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=660:duration=2",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=0.02",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=660:duration=2",
            "-filter_complex",
            "[0:a]volume=0.02[a0];[1:a]volume=1.0[a1];[2:a]volume=0.02[a2];[a0][a1][a2]concat=n=3:v=0:a=1",
            str(path),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr
    return path


def _write_placeholder_wav(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt placeholder-audio")
    return path


def _assert_walkthrough_artifacts(run_dir: Path) -> None:
    review_session = run_dir / "review-session.json"
    recipe = run_dir / "recipe.v1.json"
    ai_draft = run_dir / "ai" / "ai-draft.v1.json"
    proposed = run_dir / "timeline.proposed.v1.json"
    accepted = run_dir / "timeline.accepted.v1.json"
    manifest = run_dir / "manifest.json"
    transcript = run_dir / "exports" / "transcript.json"

    for path in (review_session, recipe, ai_draft, proposed, accepted, manifest, transcript):
        assert path.exists(), path
        assert path.stat().st_size > 0, path

    assert _read_json(review_session)["schema_version"] == "review-session.v1"
    assert _read_json(recipe)["schema_version"] == "recipe.v1"
    assert _read_json(ai_draft)["schema_version"] == "ai-draft.v1"
    assert _read_json(proposed)["schema_version"] == "timeline.v1"
    assert _read_json(accepted)["schema_version"] == "timeline.v1"
    assert _read_json(transcript)["schema_version"] == "transcript.v1"


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg/ffprobe required")
def test_quickstart_real_audio_wav_creates_walkthrough_artifacts(tmp_path):
    audio = make_silence_fixture(tmp_path / "input.wav")
    out = tmp_path / "walkthrough"

    rc = cli.main([
        "quickstart",
        "--real-audio",
        str(audio),
        "--out",
        str(out),
        "--episode-id",
        "ep-real",
    ])

    assert rc == 0
    assert (out / "raw" / "ep-real.wav").exists()
    _assert_walkthrough_artifacts(out / "runs" / "ep-real")


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg/ffprobe required")
def test_quickstart_real_audio_spiky_wav_completes_walkthrough(tmp_path):
    audio = _make_spiky_wav(tmp_path / "spiky.wav")
    out = tmp_path / "walkthrough"

    rc = cli.main([
        "quickstart",
        "--real-audio",
        str(audio),
        "--out",
        str(out),
        "--episode-id",
        "spiky-real",
    ])

    assert rc == 0
    _assert_walkthrough_artifacts(out / "runs" / "spiky-real")


def test_quickstart_real_audio_missing_path_returns_clear_audio_error(tmp_path, capsys):
    missing = tmp_path / "missing.wav"

    rc = cli.main([
        "quickstart",
        "--real-audio",
        str(missing),
        "--out",
        str(tmp_path / "walkthrough"),
    ])

    assert rc != 0
    assert "audio" in capsys.readouterr().err.lower()


def test_quickstart_real_audio_rejects_non_wav_file(tmp_path, capsys):
    text_file = tmp_path / "notes.txt"
    text_file.write_text("not audio", encoding="utf-8")

    rc = cli.main([
        "quickstart",
        "--real-audio",
        str(text_file),
        "--out",
        str(tmp_path / "walkthrough"),
    ])

    assert rc != 0
    err = capsys.readouterr().err.lower()
    assert "audio" in err
    assert "wav" in err


@pytest.mark.parametrize("episode_id", ["../escape", "with/slash", ""])
def test_quickstart_real_audio_rejects_invalid_episode_id_before_copy(tmp_path, capsys, episode_id):
    audio = _write_placeholder_wav(tmp_path / "input.wav")
    out = tmp_path / "walkthrough"
    sentinel = out / "escape.wav"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("do not delete", encoding="utf-8")

    try:
        rc = cli.main([
            "quickstart",
            "--real-audio",
            str(audio),
            "--out",
            str(out),
            "--episode-id",
            episode_id,
        ])
    except Exception as exc:  # pragma: no cover - should become a clean CLI error
        pytest.fail(f"quickstart raised before returning a validation error: {exc!r}")

    assert rc != 0
    assert sentinel.read_text(encoding="utf-8") == "do not delete"
    err = capsys.readouterr().err.lower()
    assert "episode" in err or "invalid" in err


def test_validate_real_audio_path_returns_resolved_absolute_path(tmp_path):
    audio = _write_placeholder_wav(tmp_path / "input.wav")
    link = tmp_path / "linked.wav"
    link.symlink_to(audio)

    resolved = cli._validate_real_audio_path(link)

    assert resolved == audio.resolve(strict=True)
    assert link.name not in resolved.parts


@pytest.mark.skipif(not os.environ.get("PAE_REAL_AUDIO_DIR"), reason="real audio not mounted")
def test_quickstart_real_audio_mounted_ep1_smoke(tmp_path):
    audio = Path(os.environ["PAE_REAL_AUDIO_DIR"]) / "Untitled_1 #06.wav"
    out = tmp_path / "walkthrough"

    rc = cli.main([
        "quickstart",
        "--real-audio",
        str(audio),
        "--out",
        str(out),
        "--episode-id",
        "ep1-real",
    ])

    assert rc == 0
    _assert_walkthrough_artifacts(out / "runs" / "ep1-real")


def test_walkthrough_real_podcast_script_has_valid_bash_syntax():
    script = Path("scripts/walkthrough-real-podcast.sh")

    result = subprocess.run(["bash", "-n", str(script)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    assert result.returncode == 0, result.stderr
