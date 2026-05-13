# Preview Fidelity Increment

## Prompt-to-artifact checklist
- Ralph roadmap Phase 3 → `docs/plans/2026-05-13-preview-fidelity.md`.
- Removed-segments preview fidelity → `write_preview` now builds `removed-segments-preview.mp3` from operation source ranges via FFmpeg `aselect` instead of a generic source excerpt.
- Preview metadata remains available before media failure → existing missing-input test still covers waveform metadata before error.
- `.omx/` remains local-only → not added or committed.

## Verification evidence
- Red state: targeted preview test failed because removed preview command did not use `-af aselect`.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_artifacts_subtitles_pipeline.py -p no:cacheprovider` → 14 passed.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 59 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
