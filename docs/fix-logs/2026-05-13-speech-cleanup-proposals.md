# Safe Speech Cleanup Proposals Increment

## Prompt-to-artifact checklist
- Ralph roadmap Phase 5 → `docs/plans/2026-05-13-speech-cleanup-proposals.md`.
- Conservative speech cleanup proposals → `detect_speech_cleanup_candidates` creates proposed-only `speech_cut` operations for filler/false-start transcript segments.
- Safety default preserved → `accept_safe_defaults` keeps `speech_cut` proposed.
- Manual review path extended → `review-accept` can accept selected `speech_cut` operations and records manual review provenance.
- Render safety preserved → accepted `speech_cut` operations require manual review provenance before they can affect render cuts.

## Verification evidence
- Red state: targeted tests failed because `detect_speech_cleanup_candidates` did not exist.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_silence_retake.py tests/test_artifacts_subtitles_pipeline.py tests/test_cli.py -p no:cacheprovider` → 38 passed.
- Full verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 63 passed.
- Compile verification: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
