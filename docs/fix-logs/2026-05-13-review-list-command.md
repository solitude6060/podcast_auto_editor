# Review-list command implementation log

## Scope
Phase A2 reviewer-facing CLI completion: add a command that turns timeline operations into a stable review checklist with per-operation preview links.

## Changes
- Added `review-list <timeline>` with markdown output by default.
- Added `review-list <timeline> --format json` for future UI/TUI/report integrations.
- Preview refs are resolved from `provenance.operation_preview` first, with `preview_ref` fallback for legacy timelines.
- Added TDD coverage for markdown table and JSON payload shape.

## Verification
- Targeted red test before implementation: `review-list` was an invalid command.
- Targeted green test after implementation: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_cli.py::test_review_list_cli_outputs_operation_preview_table tests/test_cli.py::test_review_list_cli_outputs_machine_readable_rows -p no:cacheprovider` → `2 passed`.
- Full regression: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `70 passed`.
- Bytecode/static syntax check: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- Lint note: `uv run ruff check podcast_auto_editor tests` was attempted but `ruff` is not part of this uv dev environment (`No such file or directory`); no new dependency added per project rule.
