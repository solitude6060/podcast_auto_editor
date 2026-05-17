import os
import subprocess
import textwrap
from pathlib import Path

from podcast_auto_editor.cli import build_parser


SCRIPT = Path("scripts/install.sh")


def test_install_script_exists_and_is_executable():
    assert SCRIPT.exists()
    assert SCRIPT.stat().st_mode & 0o111, "install.sh must be executable"


def test_quickstart_command_exists_in_parser():
    """PR-F: `podcast-auto-editor quickstart` must be a registered subcommand
    with `--out` and `--episode-id` flags."""
    parser = build_parser()
    args = parser.parse_args(["quickstart", "--out", "/tmp/q", "--episode-id", "demo"])
    assert args.command == "quickstart"
    assert args.out == "/tmp/q"
    assert args.episode_id == "demo"


def _bin_with_stub(tmp_path: Path, name: str, body: str) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    stub = bin_dir / name
    stub.write_text(body)
    stub.chmod(0o755)
    return bin_dir


def test_install_script_handles_missing_uv_clearly(tmp_path):
    """When `uv` is not on PATH, the install script must exit non-zero and
    point the user at the uv install docs — not bubble up a stack trace
    from `uv sync`. Strip just the directories containing `uv` from PATH;
    keep the standard system paths so bash + coreutils still resolve."""
    uv_in_path = subprocess.run(["which", "uv"], capture_output=True, text=True, check=False).stdout.strip()
    uv_dir = str(Path(uv_in_path).parent) if uv_in_path else ""
    keep = [
        p for p in os.environ.get("PATH", "").split(os.pathsep)
        if p and p != uv_dir
    ]
    env = {**os.environ, "PATH": os.pathsep.join(keep)}
    completed = subprocess.run(
        [str(SCRIPT.resolve())],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0, completed.stdout
    combined = (completed.stdout + completed.stderr).lower()
    assert "uv" in combined
    assert "install" in combined


def test_install_script_is_idempotent(tmp_path):
    """Run twice with a stubbed `uv` that always succeeds; the second run
    must not error. `ffmpeg` is intentionally absent so the demo-fixtures
    branch is skipped."""
    bin_dir = _bin_with_stub(
        tmp_path,
        "uv",
        textwrap.dedent(
            """
            #!/usr/bin/env bash
            # Stub uv: accept `sync --group dev` and `run python -m ...` as no-ops.
            exit 0
            """
        ).strip()
        + "\n",
    )
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"}
    for run_idx in (1, 2):
        completed = subprocess.run(
            [str(SCRIPT.resolve())],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, (
            f"run {run_idx} failed: stdout={completed.stdout!r} stderr={completed.stderr!r}"
        )
