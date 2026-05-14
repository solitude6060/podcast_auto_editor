from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_PROFILE = "rtx4090-local"

_AI_RESOURCE_PROFILES: dict[str, dict[str, Any]] = {
    "rtx4090-local": {
        "name": "rtx4090-local",
        "description": "Local-first AI stack sized for a single NVIDIA RTX 4090 workstation.",
        "local": True,
        "fallback_only": False,
        "default_enabled": True,
        "hardware": {
            "gpu": "NVIDIA RTX 4090",
            "vram_gb": 24,
            "recommended_system_ram_gb": 64,
            "scratch_disk_gb": 200,
        },
        "roles": {
            "asr": {
                "primary": "faster-whisper-large-v3",
                "fallback": "whisper.cpp-large-v3-q5_0",
                "notes": "Use CUDA/fp16 or int8_float16; transcript output must validate as transcript.v1 before write.",
            },
            "llm": {
                "primary": "qwen3-32b-q4",
                "fallback": "qwen3-14b-q4",
                "notes": "Use quantized local inference for edit reasoning, chapters, and show-note drafts; output remains proposed/review-gated.",
            },
            "audio_analysis": {
                "primary": "ffmpeg-plus-heuristics",
                "fallback": "python-stdlib-artifact-checks",
                "notes": "Safety gates stay deterministic; AI proposals cannot directly delete speech.",
            },
            "music": {
                "primary": "disabled-local-default",
                "fallback": "manual-import",
                "notes": "Music generation is out of the default local editing path; imported audio remains user-provided media.",
            },
            "image": {
                "primary": "disabled-local-default",
                "fallback": "static-html-assets",
                "notes": "Image generation is not needed for core podcast post-production.",
            },
        },
        "capabilities": ["asr", "local_llm", "audio_analysis", "review_explainability"],
        "safety": [
            "local_first",
            "no_cloud_by_default",
            "speech_edits_proposed_only",
            "transcript_validation_before_write",
            "manual_review_required_for_speech_changes",
        ],
    },
    "minimax-fallback": {
        "name": "minimax-fallback",
        "description": "Explicit non-local fallback adapter plan for MiniMax Token Plan APIs.",
        "local": False,
        "fallback_only": True,
        "default_enabled": False,
        "requires_api_key_env": "MINIMAX_API_KEY",
        "roles": {
            "text": {
                "primary": "MiniMax-M2.7",
                "fallback": "MiniMax-M2.7-highspeed",
                "notes": "Use only when explicitly requested or local LLM fails; never auto-accept edit operations.",
            },
            "music": {
                "primary": "Music-2.6",
                "fallback": "Music-Cover",
                "notes": "Optional non-local generation; generated media must be imported as reviewable user-provided assets.",
            },
            "image_understanding": {
                "primary": "MiniMax image understanding capability",
                "fallback": "manual inspection",
                "notes": "Use only for optional visual QA or screenshots, not core audio editing.",
            },
            "web_search": {
                "primary": "MiniMax web search capability",
                "fallback": "manual documentation lookup",
                "notes": "Use only for research/documentation fallback, not default runtime behavior.",
            },
        },
        "capabilities": ["text_generation", "music_generation", "music_cover", "lyrics_generation", "image_understanding", "web_search"],
        "safety": [
            "non_local_fallback_only",
            "requires_explicit_user_selection",
            "no_credentials_in_repo",
            "outputs_validate_before_write",
            "speech_edits_proposed_only",
        ],
    },
}


def get_ai_resource_profile(name: str) -> dict[str, Any]:
    try:
        return deepcopy(_AI_RESOURCE_PROFILES[name])
    except KeyError as exc:
        available = ", ".join(sorted(_AI_RESOURCE_PROFILES))
        raise ValueError(f"unknown AI resource profile: {name}; available profiles: {available}") from exc


def list_ai_resource_profiles() -> dict[str, Any]:
    profiles = []
    for name in sorted(_AI_RESOURCE_PROFILES, key=lambda item: (item != DEFAULT_PROFILE, item)):
        profile = get_ai_resource_profile(name)
        profile["default"] = name == DEFAULT_PROFILE
        profiles.append(profile)
    return {"default_profile": DEFAULT_PROFILE, "profiles": profiles}


def format_ai_resource_profiles_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# AI Resource Profiles",
        "",
        f"Default profile: `{payload['default_profile']}`",
        "",
    ]
    for profile in payload.get("profiles") or []:
        badges = []
        if profile.get("default"):
            badges.append("default")
        if profile.get("fallback_only"):
            badges.append("fallback-only")
        if profile.get("local"):
            badges.append("local")
        else:
            badges.append("non-local")
        lines.extend(
            [
                f"## {profile['name']}",
                "",
                f"- Description: {profile.get('description', '')}",
                f"- Mode: {', '.join(badges)}",
            ]
        )
        if profile.get("requires_api_key_env"):
            lines.append(f"- Required API key env: `{profile['requires_api_key_env']}`")
        hardware = profile.get("hardware") or {}
        if hardware:
            lines.append(f"- Hardware: {hardware.get('gpu')} / {hardware.get('vram_gb')}GB VRAM")
        roles = profile.get("roles") or {}
        if roles:
            lines.append("- Roles:")
            for role, details in roles.items():
                lines.append(f"  - {role}: {details.get('primary')} (fallback: {details.get('fallback')})")
        lines.append("")
    return "\n".join(lines)
