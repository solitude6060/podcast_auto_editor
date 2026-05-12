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
- FFmpeg/ffprobe are used for real media probe/render/quality measurement when available.
- Speech/retake cuts default to `proposed`; deterministic silence cuts may be safely accepted by explicit safe-default path.

## Safety policy
- No bulk acceptance of `retake_cut` operations.
- Retake auto-accept requires `auto_low_risk_speech`, confidence >= 0.90, low risk, evidence, preview, diff, recovery, and successful policy provenance.
- CLI `render` refuses proposed timelines unless `--accept-safe-defaults` is used for deterministic silence only.

## Quality gates
- Stereo: -16 LUFS ±1 LU.
- Mono: -19 LUFS ±1 LU.
- True peak <= -1.0 dBTP.
- Clipped samples measured from decoded PCM; missing metrics fail.
- A/V sync uses measured stream durations; unmeasured stream duration fails.

## TDD record
- Added regression tests for config defaults, timeline validation, silence proposals, retake policy, artifact paths, subtitles, chapters, CLI safety, FFmpeg acceptance paths, quality gates, and MP4 sync measurement.
- Architect rejection around MP4 sync fallback was resolved with a red/green regression test: missing stream durations must stay `None` and fail sync validation.

## Verification
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` => 29 passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q podcast_auto_editor tests` => passed.
- Architect final re-verification => APPROVED.

## Git hygiene
- `.omx/`, `runs/`, `artifacts/`, Python bytecode, and pytest cache are ignored.
- Commit messages should follow Lore trailers but no longer require `Co-authored-by: OmX`.
