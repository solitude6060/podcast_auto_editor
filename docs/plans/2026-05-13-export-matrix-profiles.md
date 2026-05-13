# Export matrix and mastering profiles increment

## Goal
Implement Phase A5's first production-ready slice: explicit export profiles with per-profile render outputs and quality gate reports while preserving the existing `episode.edited.wav` default artifact.

## Acceptance criteria
- Built-in profiles exist for `archive-wav`, `podcast-stereo`, and `podcast-mono`.
- Rendering generates profile-specific audio paths and stores them under `timeline.export_metadata.export_profiles`.
- Each profile runs its own quality gate and failures report the failing profile name.
- Existing compatibility fields remain: `quality_gate_report` and `edited_audio` still point at `episode.edited.wav`.
- Default behavior stays local-first and dependency-free; no new packages.

## Files
- `podcast_auto_editor/exports.py` — profile definitions and helpers.
- `podcast_auto_editor/media.py` — channel-aware audio render command.
- `podcast_auto_editor/pipeline.py` — render export matrix and metadata.
- `tests/test_exports.py` and existing render tests.
- SDD and fix log for traceability.

## Verification
- Targeted profile/render tests first.
- Full `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests`.
