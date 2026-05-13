# Per-operation Preview Pack Increment

## Prompt-to-artifact checklist
- Advanced RALPLAN Phase A2 → `docs/plans/2026-05-13-per-operation-preview-pack.md`.
- Per-operation preview metadata → `write_preview` now emits per-operation `before_after_ref` and `removed_ref` under `preview/operations/<operation_id>/` in `waveform.json`.
- Timeline operation linkage → operations without a preview now receive `preview_ref` pointing at their per-operation before/after preview path before media generation.
- Safety behavior preserved → metadata is written before FFmpeg/input errors, so review paths remain inspectable even on preview generation failure.

## Verification evidence
- Red state: targeted tests failed on missing `operation_preview` and missing operation `preview_ref` assignment.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_artifacts_subtitles_pipeline.py -p no:cacheprovider` → 18 passed.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 66 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
