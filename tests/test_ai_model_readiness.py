import json

from podcast_auto_editor.ai_models import build_model_readiness_report, format_model_readiness_markdown
from podcast_auto_editor.cli import main


def test_model_readiness_matches_ollama_tags_fixture(tmp_path):
    tags = tmp_path / "tags.json"
    tags.write_text(json.dumps({"models": [{"name": "qwen3:0.6b"}]}))

    report = build_model_readiness_report(tags_json=tags, tier="all", check_ollama=False, check_openai_api=False)

    assert report["schema_version"] == "ai-model-readiness.v1"
    by_name = {model["name"]: model for model in report["models"]}
    assert by_name["qwen3:0.6b"]["installed"] is True
    assert by_name["qwen3:32b"]["installed"] is False
    assert report["summary"]["installed"] == 1


def test_model_readiness_markdown_is_human_readable(tmp_path):
    tags = tmp_path / "tags.json"
    tags.write_text(json.dumps({"models": []}))
    markdown = format_model_readiness_markdown(build_model_readiness_report(tags_json=tags, check_ollama=False))

    assert "# Local AI Model Readiness" in markdown
    assert "qwen3:0.6b" in markdown
    assert "not installed" in markdown


def test_ai_models_readiness_cli_outputs_json_from_fixture(tmp_path, capsys):
    tags = tmp_path / "tags.json"
    tags.write_text(json.dumps({"models": [{"name": "qwen3:0.6b"}]}))

    assert main(["ai", "models", "--readiness", "--ollama-tags-json", str(tags), "--no-openai-api", "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["installed"] == 1


def test_ai_models_readiness_cli_handles_offline_ollama(capsys):
    assert main(["ai", "models", "--readiness", "--ollama-url", "http://127.0.0.1:9", "--timeout", "0.01"]) == 0

    output = capsys.readouterr().out
    assert "Ollama tags unavailable" in output


def test_model_readiness_matches_openai_compatible_models_fixture(tmp_path):
    models = tmp_path / "models.json"
    models.write_text(json.dumps({"data": [{"id": "qwen3.6-27b-turbo3"}]}))

    report = build_model_readiness_report(openai_models_json=models, tier="api-local", check_ollama=False, check_openai_api=False)

    by_name = {model["name"]: model for model in report["models"]}
    assert by_name["qwen3.6-27b-turbo3"]["installed"] is True
    assert by_name["qwen3.6-27b-turbo3"]["provider"] == "openai-compatible"
    assert by_name["qwen3.6-27b-turbo3"]["context_window"] == 128000
    assert "vision_understanding" in by_name["qwen3.6-27b-turbo3"]["capabilities"]
    assert report["summary"]["installed"] == 1


def test_model_readiness_defaults_to_existing_qwen_api_endpoint():
    report = build_model_readiness_report(tier="api-local", check_ollama=False, check_openai_api=False, env={})

    assert report["openai_base_url"] == "http://127.0.0.1:9090/v1"


def test_ai_models_readiness_cli_supports_existing_llama_cpp_api_fixture(tmp_path, capsys):
    models = tmp_path / "models.json"
    models.write_text(json.dumps({"data": [{"id": "qwen3.6-27b-turbo3"}]}))

    assert main([
        "ai",
        "models",
        "--readiness",
        "--tier",
        "api-local",
        "--openai-models-json",
        str(models),
        "--no-openai-api",
        "--no-ollama",
        "--format",
        "json",
    ]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["models"][0]["name"] == "qwen3.6-27b-turbo3"
    assert payload["models"][0]["installed"] is True
