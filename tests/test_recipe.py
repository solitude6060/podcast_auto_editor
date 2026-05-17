import json
from pathlib import Path

import pytest

from podcast_auto_editor.recipe import (
    SCHEMA_VERSION,
    RecipeError,
    apply_recipe,
    export_recipe,
)
from podcast_auto_editor.timeline import create_noop_timeline, sha256_file, write_json


def _make_run_dir(tmp_path: Path) -> tuple[Path, Path]:
    """Build a synthetic run directory + source media that mirrors `run`'s output."""
    media = tmp_path / "input.wav"
    media.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt original-audio")
    run = tmp_path / "runs" / "ep1"
    run.mkdir(parents=True)

    timeline = create_noop_timeline(
        {"path": str(media), "duration": 4.0, "sha256": sha256_file(media)},
        [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}],
    )
    timeline["operations"].append({
        "operation_id": "silence_001",
        "type": "silence_cut",
        "source_range": {"start": 1.0, "end": 2.0},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "accepted",
        "risk": "deterministic",
        "confidence": 1.0,
        "provenance": {"detector": "ffmpeg.silencedetect"},
        "preview_ref": None,
        "diff_ref": None,
        "recovery_ref": None,
    })
    write_json(run / "timeline.accepted.v1.json", timeline)
    (run / "manifest.json").write_text(
        json.dumps({
            "input": str(media),
            "episode_id": "ep1",
            "config": {"quality": {"stereo_loudness_lufs": -16.0}},
        })
    )
    return media, run


def test_recipe_export_writes_canonical_json(tmp_path):
    media, run = _make_run_dir(tmp_path)
    out = tmp_path / "recipe.json"

    result = export_recipe(run, out)

    assert result == out
    data = json.loads(out.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["source_media"]["sha256"] == sha256_file(media)
    assert data["source_media"]["duration_s"] == 4.0
    assert data["accepted_timeline"]["operations"][0]["operation_id"] == "silence_001"
    assert data["config"]["quality"]["stereo_loudness_lufs"] == -16.0
    # Keys sorted for git-friendly diffs
    assert list(data.keys()) == sorted(data.keys())


def test_recipe_export_includes_ai_draft_when_present(tmp_path):
    media, run = _make_run_dir(tmp_path)
    ai_dir = run / "ai"
    ai_dir.mkdir()
    (ai_dir / "ai-draft.v1.json").write_text(json.dumps({"schema_version": "ai-draft.v1", "chapters": []}))
    out = tmp_path / "recipe.json"

    export_recipe(run, out)

    data = json.loads(out.read_text())
    assert data["ai_draft"]["schema_version"] == "ai-draft.v1"


def test_recipe_export_omits_ai_draft_when_absent(tmp_path):
    media, run = _make_run_dir(tmp_path)
    out = tmp_path / "recipe.json"

    export_recipe(run, out)

    data = json.loads(out.read_text())
    assert data["ai_draft"] is None


def test_recipe_apply_replays_timeline_deterministically_when_hash_matches(tmp_path):
    media, run = _make_run_dir(tmp_path)
    recipe = tmp_path / "recipe.json"
    export_recipe(run, recipe)

    new_run = tmp_path / "runs" / "ep1-replay"
    apply_recipe(recipe, media, new_run)

    original = json.loads((run / "timeline.accepted.v1.json").read_text())
    replayed = json.loads((new_run / "timeline.accepted.v1.json").read_text())
    assert original == replayed


def test_recipe_apply_refuses_when_media_hash_mismatch(tmp_path):
    media, run = _make_run_dir(tmp_path)
    recipe = tmp_path / "recipe.json"
    export_recipe(run, recipe)

    other_media = tmp_path / "input-modified.wav"
    other_media.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt different-audio")

    with pytest.raises(RecipeError, match="sha256 mismatch"):
        apply_recipe(recipe, other_media, tmp_path / "runs" / "ep1-fail")


def test_recipe_apply_with_allow_media_drift_overrides_refusal(tmp_path):
    media, run = _make_run_dir(tmp_path)
    recipe = tmp_path / "recipe.json"
    export_recipe(run, recipe)

    other_media = tmp_path / "input-modified.wav"
    other_media.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt different-audio")

    out_dir = apply_recipe(
        recipe,
        other_media,
        tmp_path / "runs" / "ep1-drift",
        allow_media_drift=True,
    )

    assert (out_dir / "timeline.accepted.v1.json").exists()


def test_recipe_apply_raises_when_source_path_missing(tmp_path):
    _media, run = _make_run_dir(tmp_path)
    recipe = tmp_path / "recipe.json"
    export_recipe(run, recipe)

    with pytest.raises(RecipeError, match="source media not found"):
        apply_recipe(
            recipe,
            tmp_path / "does-not-exist.wav",
            tmp_path / "runs" / "ep1-no-media",
        )


def test_recipe_apply_rejects_unknown_schema_version(tmp_path):
    media, run = _make_run_dir(tmp_path)
    recipe = tmp_path / "recipe.json"
    export_recipe(run, recipe)

    # Tamper with schema_version
    data = json.loads(recipe.read_text())
    data["schema_version"] = "recipe.v999"
    recipe.write_text(json.dumps(data))

    with pytest.raises(RecipeError, match="schema_version"):
        apply_recipe(recipe, media, tmp_path / "runs" / "ep1-bad-schema")


def test_recipe_apply_rejects_null_schema_version(tmp_path):
    """Regression for triple review: `schema_version: null` must not slip through."""
    media, run = _make_run_dir(tmp_path)
    recipe = tmp_path / "recipe.json"
    export_recipe(run, recipe)

    data = json.loads(recipe.read_text())
    data["schema_version"] = None
    recipe.write_text(json.dumps(data))

    with pytest.raises(RecipeError, match="schema_version"):
        apply_recipe(recipe, media, tmp_path / "runs" / "ep1-null-schema")


def test_recipe_apply_raises_when_sha256_is_null_in_recipe(tmp_path):
    """Triple-review HIGH (Gemini + Codex; MiniMax MED): a recipe whose
    `source_media.sha256` is `null` (stripped, malformed, or adversarial)
    must NOT silently bypass hash verification. Previously the guard
    `if expected_sha and ...` short-circuited to False on null sha and
    accepted any media."""
    media, run = _make_run_dir(tmp_path)
    recipe = tmp_path / "recipe.json"
    export_recipe(run, recipe)

    data = json.loads(recipe.read_text())
    data["source_media"]["sha256"] = None
    recipe.write_text(json.dumps(data))

    with pytest.raises(RecipeError, match="sha256"):
        apply_recipe(recipe, media, tmp_path / "runs" / "ep1-null-sha")


def test_recipe_apply_raises_when_sha256_field_absent_in_recipe(tmp_path):
    """Same security boundary as null sha, but the field is entirely absent.
    Even with `--allow-media-drift`, a recipe without a sha256 baseline is
    not a meaningful artefact to apply — refuse instead of silent-passing."""
    media, run = _make_run_dir(tmp_path)
    recipe = tmp_path / "recipe.json"
    export_recipe(run, recipe)

    data = json.loads(recipe.read_text())
    del data["source_media"]["sha256"]
    recipe.write_text(json.dumps(data))

    with pytest.raises(RecipeError, match="sha256"):
        apply_recipe(
            recipe,
            media,
            tmp_path / "runs" / "ep1-absent-sha",
            allow_media_drift=True,
        )
