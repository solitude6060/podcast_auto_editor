from __future__ import annotations

from typing import Any

_MODELS: list[dict[str, Any]] = [
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
        "default_tier": "smoke",
        "models": models,
        "safety": {
            "auto_downloads": False,
            "gpu_shared_default": "smoke",
            "heavy_models_manual_only": True,
            "minimax_fallback_only": True,
        },
    }


def _pull_command(model_name: str) -> str:
    return f"docker compose --profile ai exec ollama ollama pull {model_name}"


def build_pull_plan(tier: str = "smoke") -> dict[str, Any]:
    catalog = build_model_catalog(tier=tier)
    commands = [_pull_command(model["name"]) for model in catalog["models"] if model["provider"] == "ollama"]
    return {
        "schema_version": "ai-model-pull-plan.v1",
        "tier": tier,
        "executes_commands": False,
        "commands": commands,
        "warnings": [
            "Manual plan only: commands are not executed by podcast-auto-editor.",
            "Use smoke tier while the GPU is shared with another project.",
            "Schedule heavy-manual pulls/runs for an explicit GPU maintenance window.",
        ],
    }


def format_model_catalog_markdown(catalog: dict[str, Any]) -> str:
    lines = [
        "# Local AI Model Catalog",
        "",
        "No models are downloaded automatically. Use the smoke tier on a shared GPU and schedule heavy-manual models for a maintenance window.",
        "",
        "| Model | Tier | Role | Est. VRAM | Shared GPU | Pull command |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for model in catalog.get("models") or []:
        shared = "yes" if model.get("gpu_shared_safe") else "no"
        lines.append(
            f"| {model['name']} | {model['tier']} | {model['role']} | {model['estimated_vram_gb']}GB | {shared} | `{_pull_command(model['name'])}` |"
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
    lines.extend(plan.get("commands") or [])
    return "\n".join(lines) + "\n"
