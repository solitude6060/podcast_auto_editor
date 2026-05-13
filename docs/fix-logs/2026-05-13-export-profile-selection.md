# Export profile selection implementation log

## Scope
A5 control-surface increment: allow config and CLI to select a subset of built-in export profiles without changing the default full export matrix.

## Changes
- Added `AppConfig.export_profiles`, defaulting to `archive-wav`, `podcast-stereo`, `podcast-mono`.
- Added export profile validation for empty/unknown profile names.
- Added `select_export_profiles()` helper in `podcast_auto_editor.exports`.
- `render()` and `run_pipeline()` now accept optional export profile overrides.
- `run` and `render` CLI commands support repeatable `--export-profile`.
- `render` validates profile names before preview/media rendering so invalid profile requests fail cleanly.

## Verification
- Red tests first: config lacked `export_profiles`, render rejected `export_profile_names`, and CLI did not handle profile overrides.
- Targeted green: export/config tests and CLI profile tests passed.
- Full regression: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `85 passed`.
