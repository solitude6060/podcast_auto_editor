from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_MODELS: list[dict[str, Any]] = [
    {
        "name": "qwen3.6-27b-turbo3",
        "tier": "api-local",
        "role": "llm-primary-api",
        "provider": "openai-compatible",
        "estimated_vram_gb": 20,
        "context_window": 128000,
        "capabilities": ["text", "vision_understanding"],
        "gpu_shared_safe": False,
        "auto_pull": False,
        "pull_command": None,
        "api_base_url_env": "LOCAL_LLM_BASE_URL",
        "model_env": "LOCAL_LLM_MODEL",
        "default_base_url": "http://127.0.0.1:9090/v1",
        "notes": "Existing llama.cpp/OpenAI-compatible API model with 128k context and VL capability. Use the already-running local endpoint; do not download through this project.",
    },
    {
        "name": "qwen3:0.6b",
        "tier": "smoke",
        "role": "llm-smoke",
        "provider": "ollama",
        "estimated_vram_gb": 2,
        "gpu_shared_safe": True,
        "auto_pull": False,
        "notes": "Small smoke model for validating Ollama wiring while another project may be using the GPU.",
    },
    {
        "name": "qwen3:14b",
        "tier": "recommended",
        "role": "llm-fallback",
        "provider": "ollama",
        "estimated_vram_gb": 10,
        "gpu_shared_safe": False,
        "auto_pull": False,
        "notes": "Recommended local fallback for chapter/show-note drafts when GPU memory is available.",
    },
    {
        "name": "qwen3:32b",
        "tier": "heavy-manual",
        "role": "llm-primary",
        "provider": "ollama",
        "estimated_vram_gb": 22,
        "gpu_shared_safe": False,
        "auto_pull": False,
        "notes": "Primary 4090-class local reasoning model; pull and run only during a GPU maintenance window.",
    },
]


def build_model_catalog(tier: str | None = None) -> dict[str, Any]:
    models = [dict(model) for model in _MODELS if tier in (None, "all", model["tier"])]
    return {
        "schema_version": "ai-model-catalog.v1",
        "default_tier": "api-local",
        "models": models,
        "safety": {
            "auto_downloads": False,
            "gpu_shared_default": "smoke",
            "existing_api_default": "qwen3.6-27b-turbo3",
            "existing_api_default_base_url": "http://127.0.0.1:9090/v1",
            "heavy_models_manual_only": True,
            "minimax_fallback_only": True,
        },
    }


def _pull_command(model_name: str) -> str:
    return f"docker compose --profile ai exec ollama ollama pull {model_name}"


def _model_pull_command(model: dict[str, Any]) -> str | None:
    if model.get("provider") != "ollama":
        return None
    return _pull_command(model["name"])


def build_pull_plan(tier: str = "smoke") -> dict[str, Any]:
    catalog = build_model_catalog(tier=tier)
    commands = [command for model in catalog["models"] if (command := _model_pull_command(model))]
    return {
        "schema_version": "ai-model-pull-plan.v1",
        "tier": tier,
        "executes_commands": False,
        "commands": commands,
        "warnings": [
            "Manual plan only: commands are not executed by podcast-auto-editor.",
            "Use api-local when your existing llama.cpp/OpenAI-compatible endpoint is already running.",
            "Use smoke tier while the GPU is shared with another project.",
            "Schedule heavy-manual pulls/runs for an explicit GPU maintenance window.",
        ],
    }


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def _ollama_model_names(data: Any) -> set[str]:
    if not isinstance(data, dict):
        return set()
    names = set()
    for item in data.get("models") or []:
        if isinstance(item, dict) and item.get("name"):
            names.add(str(item["name"]))
    return names


def _openai_model_names(data: Any) -> set[str]:
    if not isinstance(data, dict):
        return set()
    names = set()
    for item in data.get("data") or data.get("models") or []:
        if isinstance(item, dict):
            name = item.get("id") or item.get("name")
            if name:
                names.add(str(name))
    return names


def _fetch_json(url: str, timeout_s: float) -> tuple[Any | None, str | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:
            return json.loads(response.read().decode("utf-8")), None
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return None, str(exc)


def build_model_readiness_report(
    *,
    tier: str = "all",
    tags_json: str | Path | None = None,
    openai_models_json: str | Path | None = None,
    ollama_url: str = "http://127.0.0.1:11434",
    openai_base_url: str | None = None,
    timeout_s: float = 0.5,
    check_ollama: bool = True,
    check_openai_api: bool = True,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    env = dict(os.environ if env is None else env)
    openai_base_url = openai_base_url or env.get("LOCAL_LLM_BASE_URL") or "http://127.0.0.1:9090/v1"
    ollama_names: set[str] = set()
    openai_names: set[str] = set()
    warnings: list[str] = []

    if tags_json:
        ollama_names = _ollama_model_names(_load_json(tags_json))
    elif check_ollama:
        data, error = _fetch_json(ollama_url.rstrip("/") + "/api/tags", timeout_s)
        if data is None:
            warnings.append(f"Ollama tags unavailable: {error}")
        else:
            ollama_names = _ollama_model_names(data)
    else:
        warnings.append("Ollama tags check skipped.")

    if openai_models_json:
        openai_names = _openai_model_names(_load_json(openai_models_json))
    elif check_openai_api:
        data, error = _fetch_json(openai_base_url.rstrip("/") + "/models", timeout_s)
        if data is None:
            warnings.append(f"OpenAI-compatible models unavailable: {error}")
        else:
            openai_names = _openai_model_names(data)
    else:
        warnings.append("OpenAI-compatible models check skipped.")

    models = []
    for model in build_model_catalog(tier=tier)["models"]:
        provider = model["provider"]
        installed = model["name"] in (openai_names if provider == "openai-compatible" else ollama_names)
        item = dict(model)
        item["installed"] = installed
        item["source"] = "openai-compatible /v1/models" if provider == "openai-compatible" else "ollama /api/tags"
        models.append(item)
    installed_count = sum(1 for model in models if model["installed"])
    return {
        "schema_version": "ai-model-readiness.v1",
        "overall_status": "ok" if installed_count else "warning",
        "models": models,
        "summary": {"installed": installed_count, "total": len(models), "missing": len(models) - installed_count},
        "warnings": warnings,
        "openai_base_url": openai_base_url,
        "executes_commands": False,
    }


def format_model_catalog_markdown(catalog: dict[str, Any]) -> str:
    lines = [
        "# Local AI Model Catalog",
        "",
        "No models are downloaded automatically. Prefer the existing api-local llama.cpp/OpenAI-compatible endpoint when available. Use the smoke tier on a shared GPU and schedule heavy-manual models for a maintenance window.",
        "",
        "| Model | Tier | Provider | Role | Context | Est. VRAM | Shared GPU | Pull command |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for model in catalog.get("models") or []:
        shared = "yes" if model.get("gpu_shared_safe") else "no"
        command = _model_pull_command(model) or "existing API; no pull command"
        lines.append(
            f"| {model['name']} | {model['tier']} | {model['provider']} | {model['role']} | {model.get('context_window', '-')} | {model['estimated_vram_gb']}GB | {shared} | `{command}` |"
        )
    return "\n".join(lines) + "\n"


def format_pull_plan_script(plan: dict[str, Any]) -> str:
    lines = [
        "# Manual Ollama pull plan",
        f"# Tier: {plan['tier']}",
        "# Review GPU availability before running these commands.",
        "# These commands are printed only; podcast-auto-editor did not execute them.",
        "",
    ]
    if not plan.get("commands"):
        lines.append("# No Ollama pull commands for this tier; use the existing API endpoint.")
    else:
        lines.extend(plan.get("commands") or [])
    return "\n".join(lines) + "\n"


def format_model_readiness_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Local AI Model Readiness",
        "",
        f"Overall status: `{report['overall_status']}`",
        f"Installed: {report['summary']['installed']}/{report['summary']['total']}",
        "",
    ]
    for warning in report.get("warnings") or []:
        lines.append(f"- Warning: {warning}")
    if report.get("warnings"):
        lines.append("")
    lines.extend([
        "| Model | Provider | Tier | Installed | Source |",
        "| --- | --- | --- | --- | --- |",
    ])
    for model in report.get("models") or []:
        status = "installed" if model.get("installed") else "not installed"
        lines.append(f"| {model['name']} | {model['provider']} | {model['tier']} | {status} | {model['source']} |")
    return "\n".join(lines) + "\n"
