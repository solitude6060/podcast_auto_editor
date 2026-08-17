import json
from pathlib import Path

from podcast_auto_editor.ai_doctor import build_ai_doctor_report, format_ai_doctor_markdown
from podcast_auto_editor.cli import main


def test_ai_doctor_report_checks_compose_and_redacts_minimax(tmp_path, monkeypatch):
    compose = tmp_path / "compose.yaml"
    compose.write_text("""
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "127.0.0.1:11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]
""")
    binary = tmp_path / "whisper-cli"
    model = tmp_path / "ggml-large-v3-q5_0.bin"
    binary.write_text("bin")
    model.write_text("model")
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-token")

    report = build_ai_doctor_report(compose_file=compose, whisper_binary=binary, whisper_model=model, check_ollama=False)

    assert report["overall_status"] == "warning"
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["compose_file"]["status"] == "ok"
    assert checks["compose_gpu"]["status"] == "ok"
    assert checks["whisper_cpp_binary"]["status"] == "ok"
    assert checks["whisper_cpp_model"]["status"] == "ok"
    assert checks["minimax_fallback"]["status"] == "warning"
    assert "secret-token" not in json.dumps(report)


def test_ai_doctor_reports_optional_python_ai_packages(monkeypatch):
    def fake_find_spec(name):
        return object() if name == "faster_whisper" else None

    monkeypatch.setattr("podcast_auto_editor.ai_doctor.importlib.util.find_spec", fake_find_spec)

    report = build_ai_doctor_report(check_ollama=False, require_whisper=False)

    checks = {check["name"]: check for check in report["checks"]}
    assert checks["python_package_faster_whisper"]["status"] == "ok"
    assert checks["python_package_qwen_asr"]["status"] == "warning"
    assert checks["python_package_pyannote"]["status"] == "warning"


def test_ai_doctor_report_marks_missing_required_local_files(tmp_path):
    report = build_ai_doctor_report(
        compose_file=tmp_path / "missing-compose.yaml",
        whisper_binary=tmp_path / "missing-whisper-cli",
        whisper_model=tmp_path / "missing-model.bin",
        check_ollama=False,
    )

    assert report["overall_status"] == "missing"
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["compose_file"]["status"] == "missing"
    assert checks["whisper_cpp_binary"]["status"] == "missing"
    assert checks["whisper_cpp_model"]["status"] == "missing"


def test_ai_doctor_markdown_is_human_readable(tmp_path):
    report = build_ai_doctor_report(compose_file=tmp_path / "missing.yaml", check_ollama=False)
    markdown = format_ai_doctor_markdown(report)

    assert "# AI Environment Doctor" in markdown
    assert "Overall status:" in markdown
    assert "compose_file" in markdown


def test_ai_doctor_cli_outputs_json_and_exit_code(tmp_path, capsys):
    compose = tmp_path / "compose.yaml"
    compose.write_text("services: {}")

    assert main(["ai", "doctor", "--compose-file", str(compose), "--format", "json"]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_status"] == "missing"
    assert any(check["name"] == "compose_ollama" for check in payload["checks"])


def test_ai_doctor_cli_markdown_success_with_repo_compose(capsys):
    assert main(["ai", "doctor", "--no-ollama", "--optional-whisper", "--format", "markdown"]) == 0

    output = capsys.readouterr().out
    assert "# AI Environment Doctor" in output
    assert "compose_gpu" in output
