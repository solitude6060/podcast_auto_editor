# Packaging and Smoke Verification Increment

## Prompt-to-artifact checklist
- Continue development without user intervention → `docs/plans/2026-05-13-packaging-smoke.md`.
- Fresh-clone operational polish → `scripts/smoke.sh` runs uv pytest, compileall, CLI help, and optional FFmpeg demo fixtures.
- uv workflow preserved → script defaults `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor` and uses `uv run`.
- Optional FFmpeg behavior → demo fixture generation runs only when `ffmpeg` is available, otherwise skips clearly.

## Verification evidence
- Smoke script: `./scripts/smoke.sh` → 65 passed and exit 0.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 65 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
