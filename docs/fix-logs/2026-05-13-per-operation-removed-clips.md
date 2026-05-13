# Per-operation Removed Clips Increment

## Prompt-to-artifact checklist
- Continue Advanced A2 → `docs/plans/2026-05-13-per-operation-removed-clips.md`.
- Per-operation removed clip generation → `write_preview` now issues one FFmpeg `aselect` command per operation and writes to `preview/operations/<operation_id>/removed.mp3`.
- Aggregate compatibility → existing `preview/removed-segments-preview.mp3` generation remains intact.
- `.omx/` hygiene → no `.omx` files are staged or tracked.

## Verification evidence
- Red state: targeted test failed because no command wrote `preview/operations/cut1/removed.mp3`.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_artifacts_subtitles_pipeline.py -p no:cacheprovider` → 19 passed.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 67 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
