import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "walkthrough-real-podcast.sh"


def _write_fake_uv(bin_dir: Path) -> None:
    uv = bin_dir / "uv"
    uv.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
audio=""
out=""
episode="ep1-real"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --real-audio)
      audio="${2:-}"
      shift 2
      ;;
    --out)
      out="${2:-}"
      shift 2
      ;;
    --episode-id)
      episode="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
if [[ ! -f "$audio" ]]; then
  echo "audio file not found by fake uv: $audio" >&2
  exit 42
fi
mkdir -p "$out/runs/$episode/ai"
printf 'fake run\\n' > "$out/runs/$episode/review-session.json"
printf 'fake run\\n' > "$out/runs/$episode/recipe.v1.json"
printf 'fake run\\n' > "$out/runs/$episode/ai/ai-draft.v1.json"
""",
        encoding="utf-8",
    )
    uv.chmod(0o755)


def _script_env(bin_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["UV_CACHE_DIR"] = "/tmp/uv-cache-podcast-auto-editor"
    return env


def _run_script(args: list[str], *, cwd: Path, bin_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=cwd,
        env=_script_env(bin_dir),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _write_blocking_rm(bin_dir: Path, log_path: Path) -> None:
    rm = bin_dir / "rm"
    rm.write_text(
        f"""#!/usr/bin/env bash
printf '%s\\n' "$@" >> {log_path}
echo "rm blocked by test harness" >&2
exit 97
""",
        encoding="utf-8",
    )
    rm.chmod(0o755)


def test_walkthrough_real_podcast_rejects_root_out_without_removing(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "rm.log"
    _write_fake_uv(bin_dir)
    _write_blocking_rm(bin_dir, log_path)
    audio = tmp_path / "input.wav"
    audio.write_bytes(b"not used by fake rm path")

    result = _run_script(["--audio", str(audio), "--out", "/"], cwd=tmp_path, bin_dir=bin_dir)

    assert result.returncode != 0
    assert "unsafe path" in result.stderr.lower()
    assert not log_path.exists()


def test_walkthrough_real_podcast_rejects_home_out_without_removing(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "rm.log"
    _write_fake_uv(bin_dir)
    _write_blocking_rm(bin_dir, log_path)
    audio = tmp_path / "input.wav"
    audio.write_bytes(b"not used by fake rm path")

    result = _run_script(["--audio", str(audio), "--out", str(Path.home())], cwd=tmp_path, bin_dir=bin_dir)

    assert result.returncode != 0
    assert "unsafe path" in result.stderr.lower()
    assert not log_path.exists()


def test_walkthrough_real_podcast_rejects_empty_out_without_removing(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "rm.log"
    _write_fake_uv(bin_dir)
    _write_blocking_rm(bin_dir, log_path)
    audio = tmp_path / "input.wav"
    audio.write_bytes(b"not used by fake rm path")

    result = _run_script(["--audio", str(audio), "--out", ""], cwd=tmp_path, bin_dir=bin_dir)

    assert result.returncode != 0
    assert "unsafe path" in result.stderr.lower()
    assert not log_path.exists()


def test_walkthrough_real_podcast_out_is_cleaned_and_recreated_across_runs(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_uv(bin_dir)
    audio = tmp_path / "input.wav"
    audio.write_bytes(b"fake wav")
    out = tmp_path / "walkthrough"

    first = _run_script(["--audio", str(audio), "--out", str(out)], cwd=tmp_path, bin_dir=bin_dir)
    assert first.returncode == 0, first.stderr
    stale = out / "stale.txt"
    stale.write_text("stale", encoding="utf-8")

    second = _run_script(["--audio", str(audio), "--out", str(out)], cwd=tmp_path, bin_dir=bin_dir)

    assert second.returncode == 0, second.stderr
    assert not stale.exists()
    assert (out / "runs" / "ep1-real" / "review-session.json").exists()


def test_walkthrough_real_podcast_resolves_relative_audio_before_cd(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_uv(bin_dir)
    run_cwd = tmp_path / "caller"
    run_cwd.mkdir()
    audio = run_cwd / "relative-input.wav"
    audio.write_bytes(b"fake wav")
    out = tmp_path / "walkthrough"

    result = _run_script(["--audio", audio.name, "--out", str(out)], cwd=run_cwd, bin_dir=bin_dir)

    assert result.returncode == 0, result.stderr
    assert "audio file not found by fake uv" not in result.stderr
