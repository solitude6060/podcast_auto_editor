# PR-A2 real-podcast walkthrough

Date: 2026-05-17
Branch: `feature/pr-a2-real-podcast-walkthrough`

## Why

PR-A2 was deferred from the Stage 1 sequence after the synthetic walkthrough and installer work landed. Stage 1 proved the local-first pipeline on generated fixtures; PR-A2 proves the same review-session, recipe, and AI-draft walkthrough shape can be driven by a real recorded WAV while keeping the existing mock/provider defaults.

This is a confidence bridge only. Real ASR, alignment, and diarization providers remain follow-up scope from X2.1, X3.1, and X4.1.

## Constraints

- Never commit the real audio files under `/media/ma/1AF83466F83441F5/startup/ep1-test-soundtrack-20260429/`.
- Keep mock/offline providers as defaults; `--real-audio` must not silently opt into real ASR, alignment, diarization, or hosted AI.
- No new Python dependencies.
- Stay narrow: only touch the PR-A2 files named in the task.
- TDD order is mandatory: failing walkthrough tests first, then implementation.
- Generated `runs/`, `.omx/`, `.omc/`, `.venv/`, and quickstart output directories stay untracked.

## Deliverables

- `quickstart --real-audio <path>` path for using a caller-supplied WAV instead of generated demo fixtures.
- Real-audio validation with clear CLI errors for missing, non-file, or unsupported audio input.
- `tests/test_walkthrough_real_audio.py` covering synthetic WAV, invalid path, non-WAV, and optional mounted real audio.
- `scripts/walkthrough-real-podcast.sh` idempotent runner.
- `docs/walkthroughs/real-podcast-ep1.md` runbook.
- Verification evidence recorded in this plan after tests and mounted-audio walkthrough run.

## TDD test list

- `test_quickstart_real_audio_wav_creates_walkthrough_artifacts`: generate a tiny WAV fixture in `tmp_path`, run quickstart with `--real-audio`, and assert review session, recipe, AI draft, proposed timeline, accepted timeline, manifest, and transcript artifacts exist with expected `schema_version` fields.
- `test_quickstart_real_audio_missing_path_returns_clear_audio_error`: invalid input path returns non-zero and mentions audio in stderr.
- `test_quickstart_real_audio_rejects_non_wav_file`: `.txt` input returns non-zero and mentions audio/WAV in stderr.
- `test_quickstart_real_audio_mounted_ep1_smoke`: skipped unless `PAE_REAL_AUDIO_DIR` is set; runs on `Untitled_1 #06.wav` and asserts core artifacts exist and are non-empty.
- `test_walkthrough_real_podcast_script_has_valid_bash_syntax`: `bash -n scripts/walkthrough-real-podcast.sh`.

## Design decision

Extend `quickstart` with `--real-audio <path>` instead of adding a new subcommand.

Reason: PR-A2 is explicitly a real-recording variant of the existing quickstart walkthrough. Reusing quickstart preserves the already-documented artifact flow and avoids a second near-identical orchestration surface. The runner script provides the named real-podcast entry point for users while the CLI keeps one walkthrough command.

Rejected alternative: a new `walkthrough` subcommand. It would make the real-audio path more discoverable, but it would duplicate quickstart parsing, output conventions, and future maintenance for no new behavior.

## Out-of-scope

- Real ASR provider execution or accuracy measurement.
- Real alignment provider execution.
- Real diarization provider execution.
- Long-form performance benchmarking on larger recordings.
- Uploading or publishing artifacts.
- Any server/cloud collaboration feature.

## Verification

- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest tests/test_walkthrough_real_audio.py -q -p no:cacheprovider` => 5 passed, 1 skipped.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` => 271 passed, 1 skipped.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` => passed.
- Mounted-audio smoke:
  ```bash
  bash scripts/walkthrough-real-podcast.sh --audio "/media/ma/1AF83466F83441F5/startup/ep1-test-soundtrack-20260429/Untitled_1 #06.wav"
  ```
  Result: completed and produced inspection artifacts. The EP1 smoke WAV failed the existing publish loudness gate (`quality gate failed for archive-wav: loudness`), so `quickstart --real-audio` emitted a warning and wrote review/recipe/AI-draft artifacts without marking publish exports as ready.
- Mounted-audio artifact paths:
  ```text
  runs/walkthrough/runs/ep1-real/review-session.json
  runs/walkthrough/runs/ep1-real/recipe.v1.json
  runs/walkthrough/runs/ep1-real/ai/ai-draft.v1.json
  ```
- Sample JSON keys:
  ```text
  review-session.json: decisions, schema_version, source_timeline
  recipe.v1.json: accepted_timeline, ai_draft, config, generated_at, schema_version, software, source_media
  ai-draft.v1.json: base_url, chapters, dry_prompt, generated_at, max_chapters, metadata, model, notes, operation_explanations, request, retake_decisions, schema_version, show_notes, summary
  timeline.accepted.v1.json: export_metadata, media_manifest, operations, provenance, recovery, schema_version, timebase, tracks
  exports/transcript.json: provider, schema_version, segments, source_media
  ```
