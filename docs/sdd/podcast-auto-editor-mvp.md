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
- Advanced preview generation creates per-operation removed-audio clips from exact operation source ranges.
- Advanced preview generation creates per-operation before/after context clips with 2s padding around edit ranges.

## Quality gates
- Stereo: -16 LUFS ±1 LU.
- Mono: -19 LUFS ±1 LU.
- True peak <= -1.0 dBTP.
- Clipped samples measured from decoded PCM; missing metrics fail.
- A/V sync uses measured stream durations; unmeasured stream duration fails.
- Audio render uses measured two-pass FFmpeg loudnorm. Lossy podcast exports may retry with extra true-peak headroom (1 / 4 / 6 dB) only when the remaining failures are true peak or clipping; the encoded file must still pass the gates.
- If a later export profile fails, `export_metadata.quality_gate_report` is that failed profile's report (`passed: false`), not the first passing profile. `render` / `run` write `timeline.accepted.v1.json` with that metadata before exiting non-zero.

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
- Advanced Phase A2 continued with per-operation removed clip generation tests.
- Advanced Phase A2 continued with per-operation before/after context clip generation tests.
- Advanced Phase A2 added `review-list` CLI tests for markdown and JSON operation preview checklists.
- Advanced Phase A4 added operation explainability tests and report grouping by risk/detector.
- Advanced Phase A5 added export profile matrix tests for archive WAV, podcast stereo MP3, podcast mono MP3, and per-profile quality gates.
- Advanced Phase A5 added config and CLI export profile selection tests.
- Advanced Phase A6 added replayable review session tests and CLI status/decide/rebuild coverage.
- Advanced Phase A7 added static HTML report tests for escaped local operation/export artifact links.
- Advanced Phase A8 added CI/release hygiene tests for uv GitHub Actions, changelog, release template, and `.omx/` local-only checks.
- 2026-08-17 Phase 0 added two-pass loudnorm / lossy true-peak retry tests, then a regression that a later-profile quality failure must set the top-level gate to the failed report and persist it on the CLI `render` path.

## Verification
- 2026-08-17 on `docs/2026-08-17-status-sync` after Phase 0: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` => 314 passed, 11 skipped (325 collected). See `docs/reviews/2026-08-17-project-status-review.md`.
- Same session: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` => passed.
- Historical early-MVP counts below are the TDD record. They are not the current suite size.
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
