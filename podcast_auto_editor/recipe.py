from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .timeline import sha256_file

SCHEMA_VERSION = "recipe.v1"


class RecipeError(Exception):
    """Raised when a recipe export or apply fails."""


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha or None


def _package_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:
        return "unknown"
    try:
        return version("podcast-auto-editor")
    except PackageNotFoundError:
        return "unknown"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def export_recipe(run_dir: str | Path, out_path: str | Path) -> Path:
    """Bundle a run directory into a portable recipe.v1.json.

    The recipe embeds the accepted timeline, config snapshot, and optional AI
    draft so a recipient can replay the edits against the same source audio
    without the original run directory.
    """
    run_root = Path(run_dir)
    manifest_path = run_root / "manifest.json"
    accepted_path = run_root / "timeline.accepted.v1.json"
    ai_draft_path = run_root / "ai" / "ai-draft.v1.json"

    if not manifest_path.exists():
        raise RecipeError(f"manifest.json not found in run_dir: {manifest_path}")
    if not accepted_path.exists():
        raise RecipeError(f"timeline.accepted.v1.json not found in run_dir: {accepted_path}")

    manifest = _load_json(manifest_path)
    accepted_timeline = _load_json(accepted_path)

    source_path_str = manifest.get("input") if isinstance(manifest, dict) else None
    if not source_path_str:
        raise RecipeError("manifest.json is missing the `input` field")
    source_path = Path(source_path_str)
    if not source_path.exists():
        raise RecipeError(f"source media referenced in manifest not found: {source_path}")

    duration_value = accepted_timeline.get("media_manifest", {}).get("duration")
    duration_s = float(duration_value) if duration_value is not None else None

    recipe = {
        "accepted_timeline": accepted_timeline,
        "ai_draft": _load_json(ai_draft_path) if ai_draft_path.exists() else None,
        "config": manifest.get("config", {}),
        "generated_at": _iso_now(),
        "schema_version": SCHEMA_VERSION,
        "software": {
            "git_sha": _git_sha(),
            "version": _package_version(),
        },
        "source_media": {
            "duration_s": duration_s,
            "path": str(source_path),
            "sha256": sha256_file(source_path),
        },
    }

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    _dump_json(out, recipe)
    return out


def apply_recipe(
    recipe_path: str | Path,
    media_path: str | Path,
    out_dir: str | Path,
    *,
    allow_media_drift: bool = False,
) -> Path:
    """Replay a recipe.v1 against a source media file into a new run directory.

    Writes the accepted timeline, manifest, and AI draft (if present in the
    recipe). Does not invoke render — callers can run `render` separately on
    the produced run directory.
    """
    recipe_p = Path(recipe_path)
    if not recipe_p.exists():
        raise RecipeError(f"recipe not found: {recipe_p}")

    recipe_data = _load_json(recipe_p)
    if not isinstance(recipe_data, dict):
        raise RecipeError("recipe payload must be a JSON object")
    if recipe_data.get("schema_version") != SCHEMA_VERSION:
        raise RecipeError(
            f"unsupported recipe schema_version: {recipe_data.get('schema_version')!r} (expected {SCHEMA_VERSION!r})"
        )

    media = Path(media_path)
    if not media.exists():
        raise RecipeError(f"source media not found: {media}")

    expected_sha = recipe_data.get("source_media", {}).get("sha256")
    if not expected_sha:
        raise RecipeError(
            "recipe is missing source_media.sha256; cannot verify media integrity. "
            "Re-export the recipe from a complete run directory."
        )
    actual_sha = sha256_file(media)
    if expected_sha != actual_sha and not allow_media_drift:
        raise RecipeError(
            f"source media sha256 mismatch (expected {expected_sha}, got {actual_sha}); "
            "pass --allow-media-drift to override"
        )

    accepted_timeline = recipe_data.get("accepted_timeline")
    if not isinstance(accepted_timeline, dict):
        raise RecipeError("recipe is missing accepted_timeline payload")

    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    timeline_out = out_root / "timeline.accepted.v1.json"
    _dump_json(timeline_out, accepted_timeline)

    manifest_payload = {
        "applied_from_recipe": str(recipe_p.resolve()),
        "artifacts": {"accepted_timeline": str(timeline_out)},
        "config": recipe_data.get("config", {}),
        "episode_id": out_root.name,
        "input": str(media),
        "media_drift_allowed": bool(allow_media_drift and expected_sha != actual_sha),
    }
    _dump_json(out_root / "manifest.json", manifest_payload)

    ai_draft = recipe_data.get("ai_draft")
    if isinstance(ai_draft, dict):
        ai_dir = out_root / "ai"
        ai_dir.mkdir(parents=True, exist_ok=True)
        _dump_json(ai_dir / "ai-draft.v1.json", ai_draft)

    return out_root
