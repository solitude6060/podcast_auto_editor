# CI and release hygiene implementation log

## Scope
A8 increment: add repository-native CI and release hygiene while preserving local-first uv workflows and `.omx/` local-only rules.

## Changes
- Added `.github/workflows/ci.yml` for push/PR checks:
  - `uv sync --group dev`
  - `uv run --group dev pytest -q -p no:cacheprovider`
  - `uv run python -m compileall -q podcast_auto_editor tests`
  - CLI help smoke
- Added `.github/PULL_REQUEST_TEMPLATE.md` with uv verification and local-only safety checklist.
- Added `CHANGELOG.md` with Unreleased section.
- Added `docs/release-notes-template.md` for release verification and compatibility notes.
- Updated README with CI/release hygiene guidance.
- Added tests that lock CI commands, release templates, and `.omx/` safety expectations.

## Verification
- Red tests first: CI workflow, changelog, release template, PR template, and README guidance were missing.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_ci_hygiene.py -p no:cacheprovider` → `3 passed`.
- Full regression: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `100 passed`.
