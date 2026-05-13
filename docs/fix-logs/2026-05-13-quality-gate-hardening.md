# Quality Gate Hardening Increment

## Prompt-to-artifact checklist
- Ralph roadmap Phase 4 → `docs/plans/2026-05-13-quality-gate-hardening.md`.
- Publishable-quality enforcement → `render` now raises `MediaToolError` when quality gates fail instead of silently returning a failed report as successful render output.
- TDD proof → test added first in `tests/test_artifacts_subtitles_pipeline.py`; initial targeted run failed because render did not raise.

## Verification evidence
- Red state: targeted test failed with `DID NOT RAISE MediaToolError`.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_artifacts_subtitles_pipeline.py -p no:cacheprovider` → 15 passed.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 60 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
