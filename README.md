# Podcast Auto Editor

Local-first, CLI-first MVP for full-length podcast post-production.

The project uses a canonical reversible `timeline.v1` before media mutation. It is audio-first (WAV/MP3/M4A), optionally supports MP4 sync/export, and keeps automated edits inspectable through preview, diff, and recovery artifacts.

## Quickstart

```bash
python -m podcast_auto_editor probe input.wav --out runs
python -m podcast_auto_editor run input.wav --out runs
python -m podcast_auto_editor validate-transcript transcript.json
python -m podcast_auto_editor dry-run input.wav --out runs
python -m podcast_auto_editor report runs/input --format markdown
python -m podcast_auto_editor demo-fixtures --out demo-fixtures
```

FFmpeg/ffprobe are used for real media probing/rendering when installed. Core timeline, safety policy, artifact, subtitle, and chapter logic are pure Python stdlib and tested without external services.

`demo-fixtures` creates deterministic sample audio/video inputs (`demo-silence.wav`, `demo-av.mp4`) for local smoke tests and docs examples. If ffmpeg is unavailable, the command fails with a clear tool-not-found error.

## Safety policy

Speech/retake edits default to `proposed`. Auto-accept requires `auto_low_risk_speech = true`, confidence `>= 0.90`, low risk, evidence, and preview/diff/recovery artifacts. Ambiguous, overlapping, meaning-changing, censorship-like, or low-confidence edits are never auto-accepted.

For intentional human-reviewed retake removal, use the explicit review path:

```bash
python -m podcast_auto_editor review-accept runs/episode/timeline.proposed.v1.json \
  --operation-id retake_abc123 \
  --reviewer producer \
  --note "Confirmed duplicate intro" \
  --out runs/episode/timeline.reviewed.v1.json
```

Plain `accept` is still insufficient for rendering accepted `retake_cut` operations; render requires either successful auto-accept provenance or explicit manual-review provenance.

To restore accepted edits before re-rendering, use the explicit undo path:

```bash
python -m podcast_auto_editor undo runs/episode/timeline.accepted.v1.json \
  --operation-id silence_abc123 \
  --reason "Keep the dramatic pause" \
  --out runs/episode/timeline.restored.v1.json
```

Use `--all` only when intentionally restoring every currently accepted operation.

Transcript, SRT, VTT, and chapter outputs use edited-output timestamps. When accepted cuts remove source ranges, supplied transcript cues are remapped through the timeline recovery map before assets are written.

## Transcript import

`run --transcript-json` accepts either:

- a legacy JSON array of cue objects, or
- a `{"schema_version":"transcript.v1","segments":[...]}` wrapper.

Each cue must include numeric `start` and `end` fields plus string `text`. Invalid shapes fail fast before the pipeline starts, so transcript import errors are reported clearly instead of surfacing later as media or retake errors.

Timeline and config validation also fail fast: operation confidence must be 0–1, affected track IDs must exist, cut ranges must stay within media duration, accepted cuts may not overlap, and quality/retake settings must stay within supported bounds.

## Dry-run and reports

Use `dry-run` to create inspectable timeline, diff, recovery, preview metadata, transcript, subtitle, chapter, and manifest artifacts without rendering edited audio/video exports. Use `report` to summarize a run directory as Markdown or JSON before committing to a render.

Removed-segment previews are generated from the actual operation source ranges, so review audio corresponds to what the timeline proposes to remove.

Render exits with a clear quality-gate failure when loudness, true peak, clipping, or A/V sync checks fail; failed quality metadata is diagnostic, not a publishable success state.

Speech cleanup heuristics can propose filler or false-start removals as `speech_cut` operations, but these speech-changing edits stay proposed until explicitly accepted with `review-accept`.

Optional MP4 rendering preflights source audio/video stream durations and drift before export; missing or drifting source streams fail before video render.

## Development verification

```bash
uv sync --group dev
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests
./scripts/smoke.sh
```

The smoke script runs the uv test suite, compileall, CLI help, and optional FFmpeg demo fixture generation when FFmpeg is installed.
