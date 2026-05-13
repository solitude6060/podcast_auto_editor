# Export profile selection increment

## Goal
Complete A5 control surface by letting config files and CLI choose which built-in export profiles to render, while keeping default behavior backward compatible.

## Acceptance criteria
- Default config renders the full built-in matrix: `archive-wav`, `podcast-stereo`, `podcast-mono`.
- JSON config can set `export_profiles` to a non-empty list of built-in profile names.
- `render` and `run` accept repeatable `--export-profile <name>` overrides.
- Unknown profile names fail during config/selection validation before rendering.
- Timeline metadata records only selected profiles.

## Files
- `podcast_auto_editor/config.py`
- `podcast_auto_editor/exports.py`
- `podcast_auto_editor/pipeline.py`
- `podcast_auto_editor/cli.py`
- `tests/test_config.py`, `tests/test_exports.py`, `tests/test_cli.py`
