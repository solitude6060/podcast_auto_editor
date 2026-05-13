# Validation Hardening Increment

## Prompt-to-artifact checklist
- Ralph execution from RALPLAN roadmap → Phase 1 validation hardening started from `docs/plans/2026-05-13-ralplan-development-roadmap.md`.
- Timeline validation hardening → `podcast_auto_editor/timeline.py` now checks confidence range, affected track references, source bounds, media duration bounds, and overlapping accepted cuts.
- Config validation hardening → `podcast_auto_editor/config.py` now fails fast with `ConfigValidationError` for unsafe quality/retake/export settings.
- TDD proof → tests were added first in `tests/test_timeline.py` and `tests/test_config.py`; initial targeted run failed on missing `ConfigValidationError`.

## Verification evidence
- Red state: targeted tests failed before implementation because `ConfigValidationError` did not exist.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_timeline.py tests/test_config.py -p no:cacheprovider` → 11 passed.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 56 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
