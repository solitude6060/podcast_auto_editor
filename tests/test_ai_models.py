import json

from podcast_auto_editor.ai_models import build_model_catalog, build_pull_plan, format_model_catalog_markdown, format_pull_plan_script
from podcast_auto_editor.cli import main


def test_model_catalog_contains_resource_tiers_and_manual_heavy_models():
    catalog = build_model_catalog()
    tiers = {model["tier"] for model in catalog["models"]}

    assert {"smoke", "recommended", "heavy-manual"}.issubset(tiers)
    assert any(model["gpu_shared_safe"] for model in catalog["models"] if model["tier"] == "smoke")
    assert all(not model["auto_pull"] for model in catalog["models"])
    assert all(not model["gpu_shared_safe"] for model in catalog["models"] if model["tier"] == "heavy-manual")


def test_pull_plan_returns_commands_without_executing_shell(monkeypatch):
    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("pull plan must not execute shell commands")

    monkeypatch.setattr("subprocess.run", fake_run)
    plan = build_pull_plan(tier="smoke")

    assert called is False
    assert plan["tier"] == "smoke"
    assert plan["commands"]
    assert all(command.startswith("docker compose --profile ai exec ollama ollama pull ") for command in plan["commands"])


def test_model_catalog_markdown_warns_about_shared_gpu():
    markdown = format_model_catalog_markdown(build_model_catalog())

    assert "# Local AI Model Catalog" in markdown
    assert "shared GPU" in markdown
    assert "heavy-manual" in markdown


def test_pull_plan_script_is_comment_first_and_manual():
    script = format_pull_plan_script(build_pull_plan(tier="recommended"))

    assert script.startswith("# Manual Ollama pull plan")
    assert "ollama pull" in script
    assert "set -e" not in script


def test_ai_models_cli_outputs_json_for_smoke_tier(capsys):
    assert main(["ai", "models", "--tier", "smoke", "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["models"]
    assert {model["tier"] for model in payload["models"]} == {"smoke"}


def test_ai_models_cli_outputs_pull_plan_without_execution(capsys):
    assert main(["ai", "models", "--tier", "smoke", "--pull-plan"]) == 0

    output = capsys.readouterr().out
    assert "# Manual Ollama pull plan" in output
    assert "qwen" in output.lower()
