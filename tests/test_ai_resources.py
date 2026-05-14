import json

from podcast_auto_editor.ai_resources import DEFAULT_PROFILE, get_ai_resource_profile, list_ai_resource_profiles, format_ai_resource_profiles_markdown
from podcast_auto_editor.cli import main


def test_rtx4090_local_profile_is_default_and_local():
    profile = get_ai_resource_profile("rtx4090-local")

    assert DEFAULT_PROFILE == "rtx4090-local"
    assert profile["local"] is True
    assert profile["fallback_only"] is False
    assert profile["hardware"]["gpu"] == "NVIDIA RTX 4090"
    assert profile["hardware"]["vram_gb"] == 24
    assert profile["roles"]["asr"]["primary"] == "faster-whisper-large-v3"
    assert profile["roles"]["llm"]["primary"] == "qwen3-32b-q4"


def test_minimax_profile_is_non_local_fallback_only():
    profile = get_ai_resource_profile("minimax-fallback")

    assert profile["local"] is False
    assert profile["fallback_only"] is True
    assert profile["requires_api_key_env"] == "MINIMAX_API_KEY"
    assert profile["default_enabled"] is False
    assert "text_generation" in profile["capabilities"]
    assert "music_generation" in profile["capabilities"]


def test_list_profiles_marks_default_once():
    payload = list_ai_resource_profiles()

    assert payload["default_profile"] == "rtx4090-local"
    assert {profile["name"] for profile in payload["profiles"]} == {"rtx4090-local", "minimax-fallback"}
    assert [profile["default"] for profile in payload["profiles"]].count(True) == 1


def test_unknown_ai_resource_profile_fails_clearly():
    try:
        get_ai_resource_profile("cloud-first")
    except ValueError as exc:
        assert "unknown AI resource profile: cloud-first" in str(exc)
    else:
        raise AssertionError("expected profile error")


def test_format_ai_resource_profiles_markdown_includes_fallback_warning():
    markdown = format_ai_resource_profiles_markdown(list_ai_resource_profiles())

    assert "# AI Resource Profiles" in markdown
    assert "rtx4090-local" in markdown
    assert "minimax-fallback" in markdown
    assert "fallback-only" in markdown


def test_ai_resources_cli_outputs_json(capsys):
    assert main(["ai", "resources", "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["default_profile"] == "rtx4090-local"
    assert payload["profiles"][0]["name"] == "rtx4090-local"


def test_ai_resources_cli_filters_profile(capsys):
    assert main(["ai", "resources", "--profile", "minimax-fallback", "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["profiles"] == [get_ai_resource_profile("minimax-fallback")]


def test_ai_resources_cli_rejects_unknown_profile(capsys):
    assert main(["ai", "resources", "--profile", "missing"]) == 1

    assert "unknown AI resource profile: missing" in capsys.readouterr().err
