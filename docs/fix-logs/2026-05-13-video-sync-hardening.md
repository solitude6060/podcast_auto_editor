# Video Sync Hardening Increment

## Prompt-to-artifact checklist
- Continue planning/development without user intervention → `docs/plans/2026-05-13-video-sync-hardening.md`.
- Source MP4 sync preflight → `validate_source_av_sync` checks source timeline audio/video duration availability and drift before `render_video`.
- Output sync diagnostics → `measure_av_sync` now reports measured audio/video durations when available.
- Render safety → `render` raises `MediaToolError` before video render if source A/V sync validation fails.
- `.omx/` stays local-only → final git checks verify empty tracked `.omx`.

## Verification evidence
- Red state: targeted tests failed because `validate_source_av_sync` did not exist.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_media_sync.py tests/test_artifacts_subtitles_pipeline.py -p no:cacheprovider` → 21 passed.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 65 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
