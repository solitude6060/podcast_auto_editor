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
python -m podcast_auto_editor validate-run --timeline runs/input/timeline.proposed.v1.json --transcript-json transcript.json
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

Use `validate-run` as a read-only preflight before processing media:

```bash
uv run python -m podcast_auto_editor validate-run \
  --config config.json \
  --timeline runs/episode/timeline.proposed.v1.json \
  --transcript-json transcript.json
```

When a timeline media duration or explicit `--duration` is available, transcript cues that extend past the media duration are rejected before any run artifact is written.

## Dry-run and reports

Use `dry-run` to create inspectable timeline, diff, recovery, preview metadata, transcript, subtitle, chapter, and manifest artifacts without rendering edited audio/video exports. Use `report` to summarize a run directory as Markdown or JSON before committing to a render.

Removed-segment previews are generated from the actual operation source ranges, so review audio corresponds to what the timeline proposes to remove.

Render exits with a clear quality-gate failure when loudness, true peak, clipping, or A/V sync checks fail; failed quality metadata is diagnostic, not a publishable success state.

Speech cleanup heuristics can propose filler or false-start removals as `speech_cut` operations, but these speech-changing edits stay proposed until explicitly accepted with `review-accept`.

Optional MP4 rendering preflights source audio/video stream durations and drift before export; missing or drifting source streams fail before video render.

## AI assist and explainability

Use `ai draft` to generate review-only artifact suggestions from timeline operations + transcript:

```bash
uv run python -m podcast_auto_editor ai draft \
  --timeline runs/episode/timeline.proposed.v1.json \
  --transcript-json runs/episode/transcript.json \
  --dry-prompt \
  --format json
```

The draft output is written to `ai/ai-draft.v1.json` under the timeline directory by default.

`--dry-run` is an alias for `--dry-prompt` (and implied `--no-net`) for offline or CI-safe runs.

For per-operation explainability, use:

```bash
uv run python -m podcast_auto_editor explain runs/episode/timeline.proposed.v1.json \
  --operation-id speech_abc123 \
  --with-ai \
  --transcript-json runs/episode/transcript.json \
  --dry-prompt \
  --format json
```

The server-side AI calls are disabled automatically in `--dry-prompt` / `--dry-run`.

## Docker AI-stack e2e smoke check

Run the local AI stack e2e check script:

```bash
./scripts/e2e-docker-ai-stack.sh --dry-run
./scripts/e2e-docker-ai-stack.sh
```

The script brings up Compose app + ollama profiles (when available), runs a smoke CLI check, and performs clean shutdown.

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
`review serve` also exposes a compact Run Dashboard (status, next operation, AI draft link/status, and artifact links).
`review launcher` writes local launcher files that start the same localhost-only review server; generated launchers are local artifacts and should not be committed.

## AI resource profiles

The default AI plan is local-first for a single RTX 4090 workstation:

```bash
uv run python -m podcast_auto_editor ai resources --format markdown
uv run python -m podcast_auto_editor ai resources --profile rtx4090-local --format json
```

`rtx4090-local` is the default profile for local ASR, local LLM reasoning, and deterministic audio analysis. `minimax-fallback` is documented as an explicit non-local fallback only; it requires `MINIMAX_API_KEY` and is never enabled implicitly.

### Optional faster-whisper local ASR

For the RTX 4090 profile, install optional ASR dependencies in your local environment and select `faster-whisper-local` explicitly:

```bash
uv run python -m podcast_auto_editor transcribe input.wav \
  --provider faster-whisper-local \
  --model large-v3 \
  --device cuda \
  --compute-type float16 \
  --out transcript.json
```

`faster-whisper-local` is not a core dependency. If `faster_whisper` is not installed, the command fails before writing `transcript.json`. The deterministic `stub` provider remains the default for tests and dependency-free smoke checks.

### Optional whisper.cpp local ASR

`whisper-cpp-local` is the dependency-light local fallback for users who manage their own `whisper.cpp` build and GGML model files:

```bash
uv run python -m podcast_auto_editor transcribe input.wav \
  --provider whisper-cpp-local \
  --binary /path/to/whisper-cli \
  --model-path /models/ggml-large-v3-q5_0.bin \
  --language zh \
  --threads 8 \
  --out transcript.json
```

The provider requires explicit local paths and runs `whisper.cpp` with JSON output enabled. Missing binaries, missing models, failed commands, invalid JSON, or invalid transcript segments fail before `transcript.json` is written.

## Docker Compose local AI stack

For containerized local development and optional RTX 4090 AI services, see [`docs/docker-compose-ai-stack.md`](docs/docker-compose-ai-stack.md):

```bash
cp .env.example .env
docker compose --profile ai up -d ollama app
docker compose --profile ai exec app uv run --group dev pytest -q -p no:cacheprovider
```

The compose stack keeps `ollama` bound to localhost, uses NVIDIA GPU reservations for the local AI service, and leaves model files, `.env`, generated runs, and `.omx` outside version control.

Check local AI wiring without downloading models:

```bash
uv run python -m podcast_auto_editor ai doctor --optional-whisper --format markdown
docker compose --profile ai exec app uv run python -m podcast_auto_editor ai doctor --optional-whisper
```

If another project is using the GPU, keep checks lightweight: use `--no-ollama` to skip the live Ollama probe, pull models manually only during an agreed maintenance window, and prefer smaller smoke models before loading 30B-class local LLMs.

Inspect the local model catalog and print manual pull commands without executing downloads:

```bash
uv run python -m podcast_auto_editor ai models --format markdown
uv run python -m podcast_auto_editor ai models --tier api-local --pull-plan
uv run python -m podcast_auto_editor ai models --tier smoke --pull-plan
LOCAL_LLM_BASE_URL=http://127.0.0.1:9090/v1 \
  uv run python -m podcast_auto_editor ai models --readiness --tier api-local --no-ollama
```

`api-local` is for an existing llama.cpp/OpenAI-compatible API model such as `qwen3.6-27b-turbo3`; it prints no download command and only checks `/v1/models` when asked for readiness.
