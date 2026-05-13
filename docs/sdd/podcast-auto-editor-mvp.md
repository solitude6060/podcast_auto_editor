# SDD: Podcast Auto Editor MVP

## Goal
Build a local-first, CLI-first, audio-first podcast auto-editor MVP with reversible timeline edits, preview/diff/recovery artifacts, publishable audio quality gates, transcript/subtitle/chapter outputs, and optional MP4 sync export.

## Source requirements
- Deep interview spec and ralplan artifacts were generated under `.omx/` during local planning.
- `.omx/` is intentionally ignored and must not be pushed.
- This SDD is the tracked repository summary of the approved plan.

## Architecture
- Python stdlib package: `podcast_auto_editor`.
- CLI entrypoint: `python -m podcast_auto_editor` / `podcast-auto-editor`.
- Canonical `timeline.v1` JSON is the source of truth before media mutation.
- Transcript/subtitle/chapter assets use edited-output timestamps derived from `recovery.source_to_output`.
- Imported transcript JSON is validated before pipeline execution and may use either a legacy segment array or `transcript.v1` wrapper.
- FFmpeg/ffprobe are used for real media probe/render/quality measurement when available.
- Speech/retake cuts default to `proposed`; deterministic silence cuts may be safely accepted by explicit safe-default path.

## Safety policy
- No bulk acceptance of `retake_cut` operations.
- Retake auto-accept requires `auto_low_risk_speech`, confidence >= 0.90, low risk, evidence, preview, diff, recovery, and successful policy provenance.
- Explicit human retake acceptance is supported only through `review-accept`, which requires selected operation IDs and records reviewer/note/timestamp provenance.
- CLI `render` refuses proposed timelines unless `--accept-safe-defaults` is used for deterministic silence only.
- CLI `render` refuses accepted `retake_cut` operations unless they carry either successful auto-accept provenance or explicit manual-review provenance.
- CLI `undo` restores accepted operations to `proposed` only with explicit operation IDs or `--all`, records undo provenance, and rebuilds recovery maps.
- Timeline validation rejects invalid confidence, unknown track IDs, out-of-bounds ranges, media-duration overflow, and overlapping accepted cuts before render.
- Config validation rejects unsafe quality, retake, and unsupported export settings at load time.
- CLI `dry-run` writes inspection artifacts without edited media exports, and CLI `report` summarizes run artifacts for producer review.
- Removed-segments preview uses actual operation source ranges, not a generic source excerpt.
- Render fails when required quality gates fail, instead of treating failed quality metadata as success.
- Speech cleanup heuristics may propose filler/false-start `speech_cut` operations, but they remain proposed and require manual review before render.
- MP4 render preflights source audio/video duration and drift before video export, and output sync reports include measured stream durations.
- `scripts/smoke.sh` provides a fresh-clone local verification path over uv tests, compileall, CLI help, and optional FFmpeg fixtures.
- Advanced preview metadata includes per-operation before/after and removed-audio review refs under `preview/operations/<operation_id>/`.

## Quality gates
- Stereo: -16 LUFS ±1 LU.
- Mono: -19 LUFS ±1 LU.
- True peak <= -1.0 dBTP.
- Clipped samples measured from decoded PCM; missing metrics fail.
- A/V sync uses measured stream durations; unmeasured stream duration fails.

## TDD record
- Added regression tests for config defaults, timeline validation, silence proposals, retake policy, artifact paths, subtitles, chapters, CLI safety, FFmpeg acceptance paths, quality gates, and MP4 sync measurement.
- Architect rejection around MP4 sync fallback was resolved with a red/green regression test: missing stream durations must stay `None` and fail sync validation.
- Next increment added red/green tests for explicit retake review acceptance, no-bulk review acceptance, and render refusal for plain accepted retakes without review provenance.
- Next increment added red/green tests for transcript cue remapping through recovery maps, including shifted, dropped, and split cues after accepted cuts.
- Team follow-up added tests for transcript import validation, enriched preview/diff metadata, and deterministic ffmpeg demo fixture generation.
- RALPLAN follow-up added tests for explicit undo scope, selected undo, all-accepted undo, non-accepted selection rejection, and recovery rebuilds.
- Ralph Phase 1 added validation hardening tests for timeline bounds/track refs/overlaps and config fail-fast behavior.
- Ralph Phase 2 added dry-run/report tests for no-render inspection artifacts and Markdown/JSON run reports.
- Ralph Phase 3 added preview fidelity tests for FFmpeg `aselect` over removed operation ranges.
- Ralph Phase 4 added quality-gate fail-fast tests for render output.
- Ralph Phase 5 added proposed-only speech cleanup tests and manual-review render safety for `speech_cut`.
- Follow-up Phase 6 added source A/V sync preflight and measured duration diagnostics.
- Follow-up Phase 7 added smoke-test script coverage for local operational verification.
- Advanced Phase A2 added per-operation preview metadata/ref attachment tests.

## Verification
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` => 29 passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q podcast_auto_editor tests` => passed.
- Architect final re-verification => APPROVED.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` => 33 passed after retake review workflow increment.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` => 35 passed after transcript time-remap increment.
- Team follow-up verification is recorded in `docs/fix-logs/2026-05-13-team-followup.md`.

## Git hygiene
- `.omx/`, `runs/`, `artifacts/`, Python bytecode, and pytest cache are ignored.
- Commit messages should follow Lore trailers but no longer require `Co-authored-by: OmX`.

## Development environment
Development is managed with `uv`:

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests
```

`uv.lock` is tracked for reproducibility. `.venv/` remains ignored.
