# Podcast Auto Editor

繁體中文版本：[`README.zh-TW.md`](README.zh-TW.md)

Local-first, CLI-first MVP for full-length podcast post-production.

The project uses a canonical reversible `timeline.v1` before media mutation. It is audio-first (WAV/MP3/M4A), optionally supports MP4 sync/export, and keeps automated edits inspectable through preview, diff, and recovery artifacts.

## Quickstart

```bash
python -m podcast_auto_editor probe input.wav --out runs
python -m podcast_auto_editor run input.wav --out runs
python -m podcast_auto_editor validate-transcript transcript.json
python -m podcast_auto_editor transcribe input.wav --provider stub --out transcript.json
python -m podcast_auto_editor dry-run input.wav --out runs
python -m podcast_auto_editor report runs/input --format markdown
python -m podcast_auto_editor project init my-show --name "My Show"
python -m podcast_auto_editor batch dry-run ep1.wav ep2.wav --out runs
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

Use `transcribe` to generate a `transcript.v1` JSON file through a local provider boundary:

```bash
uv run python -m podcast_auto_editor transcribe input.wav --provider stub --out transcript.json
```

The built-in `stub` provider is deterministic and dependency-free for tests and workflow integration. Real ASR providers should be added later as optional adapters; provider output is validated before any transcript file is written.

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

## Project and batch dry-run workflow

Use `project init` to create a local project manifest outside `.omx`:

```bash
uv run python -m podcast_auto_editor project init my-show --name "My Show"
```

Use `batch dry-run` to inspect multiple episodes without rendering edited media exports:

```bash
uv run python -m podcast_auto_editor batch dry-run ep1.wav ep2.wav --out runs
```

The command writes aggregate reports to `runs/batch/batch-report.json` and `runs/batch/batch-report.md`. Failed episodes are recorded and later episodes continue by default; pass `--fail-fast` to stop after the first failure.

## Development verification

```bash
uv sync --group dev
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests
./scripts/smoke.sh
```

The smoke script runs the uv test suite, compileall, CLI help, and optional FFmpeg demo fixture generation when FFmpeg is installed.

Per-operation preview metadata is recorded under `preview/operations/<operation_id>/` so review tools can link each proposed edit to its own before/after and removed-audio refs.

When FFmpeg is available, preview generation also writes per-operation removed-audio clips at `preview/operations/<operation_id>/removed.mp3` using the exact operation source range.

Per-operation before/after clips are generated with context padding around each edit at `preview/operations/<operation_id>/before-after.mp3` when FFmpeg is available.

## CI and release hygiene

GitHub Actions runs the same uv-managed checks used locally: pytest, compileall, and a CLI help smoke. Keep `./scripts/smoke.sh` as the local pre-push command because it also exercises optional FFmpeg demo fixture generation when FFmpeg is installed.

Release preparation should update `CHANGELOG.md` and use `docs/release-notes-template.md` for verification notes, compatibility notes, and local-only safety checks. `.omx/`, generated run artifacts, virtualenvs, and caches must remain untracked.

### Local review UI

After generating a run directory, use the scriptable review helper or local-only review server:

```bash
uv run python -m podcast_auto_editor review next runs/episode/review-session.json   --timeline runs/episode/timeline.proposed.v1.json
uv run python -m podcast_auto_editor review serve runs/episode
uv run python -m podcast_auto_editor review launcher runs/episode --out runs/episode/open-review-ui.sh --desktop-out runs/episode/open-review-ui.desktop
```

`review serve` binds to `127.0.0.1` by default and writes decisions to the same `review-session.json` used by the CLI.
`review launcher` writes local launcher files that start the same localhost-only review server; generated launchers are local artifacts and should not be committed.

## AI resource profiles

The default AI plan is local-first for a single RTX 4090 workstation:

```bash
uv run python -m podcast_auto_editor ai resources --format markdown
uv run python -m podcast_auto_editor ai resources --profile rtx4090-local --format json
```

`rtx4090-local` is the default profile for local ASR, local LLM reasoning, and deterministic audio analysis. `minimax-fallback` is documented as an explicit non-local fallback only; it requires `MINIMAX_API_KEY` and is never enabled implicitly.
