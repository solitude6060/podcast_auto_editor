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
