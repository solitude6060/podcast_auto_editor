# Review-list command increment

## Goal
Complete Phase A2's reviewer-facing CLI surface by adding a `review-list` command that summarizes timeline operations and links each row to per-operation preview assets.

## Acceptance criteria
- `podcast-auto-editor review-list <timeline>` reads any valid timeline JSON.
- Markdown output prints a stable operation table with operation id, type, state, risk, confidence, source range, preview path, and removed path.
- JSON output returns machine-readable rows for future UI/TUI/report integrations.
- Preview paths prefer `provenance.operation_preview.before_after_ref` / `removed_ref`, then fall back to `preview_ref` where available.
- Tests are written first and pass under `uv run --group dev pytest`.

## Files
- `tests/test_cli.py` — regression tests for markdown and JSON review-list output.
- `podcast_auto_editor/cli.py` — parser entry and formatting helpers.
- `docs/sdd/podcast-auto-editor-mvp.md` — SDD trace update.
- `docs/fix-logs/2026-05-13-review-list-command.md` — implementation/verification log.

## Verification
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider`
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests`
- `git ls-files .omx` remains empty.
