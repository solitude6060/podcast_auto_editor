from __future__ import annotations

from pathlib import Path
from typing import Any

SCHEMA_VERSION = "recipe.v1"


class RecipeError(Exception):
    """Raised when a recipe export or apply fails."""


def export_recipe(run_dir: str | Path, out_path: str | Path) -> Path:
    """Bundle a run directory into a portable recipe.v1.json. Stub until PR-G implementation lands."""
    raise NotImplementedError("export_recipe not implemented; PR-G in progress")


def apply_recipe(
    recipe_path: str | Path,
    media_path: str | Path,
    out_dir: str | Path,
    *,
    allow_media_drift: bool = False,
) -> Path:
    """Replay a recipe.v1 against a source media file into a new run directory. Stub until PR-G implementation lands."""
    raise NotImplementedError("apply_recipe not implemented; PR-G in progress")
