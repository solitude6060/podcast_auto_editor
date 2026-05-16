import os
import textwrap
from pathlib import Path
import subprocess


def test_e2e_docker_ai_stack_script_exists_and_has_dry_run():
    script = Path("scripts/e2e-docker-ai-stack.sh")

    assert script.exists()
    assert script.stat().st_mode & 0o111
    text = script.read_text()
    assert "DRY-RUN" in text
    assert "docker compose -f" in text
    assert "ai resources --format json" in text


def test_e2e_docker_ai_stack_script_dry_run():
    script = Path("scripts/e2e-docker-ai-stack.sh")
    completed = subprocess.run([str(script), "--dry-run"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "DRY-RUN:" in completed.stdout
    assert "docker compose -f" in completed.stdout


def test_e2e_script_app_only_fallback_exits_zero(tmp_path):
    """Regression for review: when full-stack `up -d ollama app` fails but
    `up -d --no-deps app` succeeds, the script must still exit 0. Previously
    the script unconditionally waited for ollama afterwards and was killed by
    `set -e` when ollama timed out, masking the intended graceful fallback."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker_stub = bin_dir / "docker"
    docker_stub.write_text(
        textwrap.dedent(
            """
            #!/usr/bin/env bash
            args="$*"
            case "$args" in
              "compose version") exit 0 ;;
              *"up -d ollama app"*) exit 1 ;;
              *"up -d --no-deps app"*) exit 0 ;;
              *"ps --services --filter status=running"*)
                echo "app"
                exit 0 ;;
              *"down -v"*) exit 0 ;;
              *"exec app"*) exit 0 ;;
              *) exit 0 ;;
            esac
            """
        ).strip()
        + "\n"
    )
    docker_stub.chmod(0o755)

    script = Path("scripts/e2e-docker-ai-stack.sh").resolve()
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"}
    completed = subprocess.run(
        [str(script)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, (
        f"exit={completed.returncode}\nstdout={completed.stdout!r}\nstderr={completed.stderr!r}"
    )
