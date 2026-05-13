# Per-operation Before/After Clips Increment

## Prompt-to-artifact checklist
- Continue Advanced A2 → `docs/plans/2026-05-13-per-operation-before-after-clips.md`.
- Per-operation before/after clip generation → `write_preview` now writes `preview/operations/<operation_id>/before-after.mp3` from the source range plus 2s context padding.
- Per-operation removed clips preserved → existing removed clip and aggregate removed preview still run.
- `.omx/` hygiene → no `.omx` files are staged or tracked.

## Verification evidence
- Red state: targeted test failed because no command wrote `preview/operations/cut1/before-after.mp3`.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_artifacts_subtitles_pipeline.py -p no:cacheprovider` → 20 passed.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 68 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
