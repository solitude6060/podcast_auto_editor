# Dry-run and Report Workflow Increment

## Prompt-to-artifact checklist
- Ralph roadmap Phase 2 → `docs/plans/2026-05-13-dry-run-report-workflow.md`.
- Dry-run inspection workflow → CLI `dry-run` writes proposed/accepted timelines, diff, recovery, preview metadata, transcript/subtitle/chapter assets, and manifest without edited media exports.
- Producer report workflow → CLI `report` emits JSON or Markdown with edit counts, removed duration, quality status, derived assets, and warnings.
- TDD proof → tests were added first in `tests/test_cli.py`; initial targeted run failed because `dry-run` and `report` commands did not exist.

## Verification evidence
- Red state: targeted CLI tests failed on invalid choices `dry-run` and `report`.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_cli.py -p no:cacheprovider` → 14 passed.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 58 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
