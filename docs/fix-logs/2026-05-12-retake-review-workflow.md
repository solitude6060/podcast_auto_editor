# Retake Review Workflow Increment

## Prompt-to-artifact checklist
- Continue planning and development → `docs/plans/2026-05-12-retake-review-workflow.md`.
- Preserve SDD/TDD discipline → failing tests were added before implementation in `tests/test_cli.py` and `tests/test_artifacts_subtitles_pipeline.py`.
- Keep AI auto-editing low-risk → `review-accept` requires explicit operation IDs, reviewer provenance, and does not bulk-accept retakes.
- Keep render safety → accepted `retake_cut` operations now require successful auto-accept provenance or explicit manual-review provenance.
- Keep uv dev environment → verification uses `uv run --group dev`.

## Verification evidence
- Initial targeted test run failed on missing `retake_operation_is_render_safe`, confirming red TDD state.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_cli.py tests/test_artifacts_subtitles_pipeline.py -p no:cacheprovider` → 13 passed.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 33 passed.

## Notes
This increment intentionally leaves media rendering unchanged and stores manual review data inside existing `timeline.v1` operation provenance to avoid schema churn.
