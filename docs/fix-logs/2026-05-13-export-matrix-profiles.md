# Export matrix and mastering profiles implementation log

## Scope
Phase A5 first increment: render explicit local export profiles and persist per-profile quality reports while preserving the existing default `episode.edited.wav` contract.

## Changes
- Added `podcast_auto_editor/exports.py` with built-in `archive-wav`, `podcast-stereo`, and `podcast-mono` profiles.
- Render now outputs:
  - `exports/episode.edited.wav` for backward-compatible archive WAV.
  - `exports/episode.podcast-stereo.mp3`.
  - `exports/episode.podcast-mono.mp3`.
- Each profile stores a `quality_gate_report` under `export_metadata.export_profiles`.
- Quality failures now name the failing profile, for example `quality gate failed for podcast-stereo: loudness`.
- Compatibility metadata remains: `export_metadata.edited_audio` and `export_metadata.quality_gate_report` still point to the archive WAV/default gate.
- Audio render command now passes `-ac <channels>` so mono/stereo profiles are explicit.

## Verification
- Red test before implementation: `tests/test_exports.py` failed because `podcast_auto_editor.exports` was missing.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_exports.py tests/test_artifacts_subtitles_pipeline.py::test_render_fails_when_quality_gate_fails tests/test_artifacts_subtitles_pipeline.py::test_render_fails_before_video_render_when_source_sync_invalid -p no:cacheprovider` → `5 passed`.
- Full regression: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `79 passed`.
