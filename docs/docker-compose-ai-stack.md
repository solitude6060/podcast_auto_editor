# Docker Compose Local AI Stack

Traditional Chinese version: [`docker-compose-ai-stack.zh-TW.md`](docker-compose-ai-stack.zh-TW.md)

This repository includes a local-first Docker Compose stack for development, smoke tests, and optional RTX 4090 AI services.

## Services

- `app`: Python/uv development container for `podcast_auto_editor`.
- `ollama`: optional local GPU LLM service, bound to `127.0.0.1:11434`.

The stack does not include model weights, credentials, generated runs, or `.omx` state in version control.

## Prerequisites

- Docker Engine with Compose v2.
- NVIDIA driver and NVIDIA Container Toolkit on the host for GPU access.
- An RTX 4090 or compatible NVIDIA GPU for the `ollama` profile.

## Start the local AI stack

```bash
cp .env.example .env
mkdir -p runs models third_party/whisper.cpp/build/bin
docker compose --profile ai up -d ollama app
```

Run tests inside the app container:

```bash
docker compose --profile ai exec app \
  uv run --group dev pytest -q -p no:cacheprovider
```

Run the CLI:

```bash
docker compose --profile ai exec app \
  uv run python -m podcast_auto_editor ai resources --format markdown
```

Run a lightweight AI environment doctor:

```bash
docker compose --profile ai exec app \
  uv run python -m podcast_auto_editor ai doctor --optional-whisper --format markdown
```

When another project is using the GPU, avoid heavy probes:

```bash
uv run python -m podcast_auto_editor ai doctor --no-ollama --optional-whisper
```

Model downloads are intentionally manual. Pull small smoke models first and schedule large model pulls/runs for a maintenance window:

```bash
uv run python -m podcast_auto_editor ai models --tier api-local --pull-plan
LOCAL_LLM_BASE_URL=http://127.0.0.1:9090/v1 \
  uv run python -m podcast_auto_editor ai models --readiness --tier api-local --no-ollama
uv run python -m podcast_auto_editor ai models --tier smoke --pull-plan
docker compose --profile ai exec ollama ollama pull qwen3:0.6b
# Later, when GPU memory is available:
# docker compose --profile ai exec ollama ollama pull qwen3:32b
```

Use `api-local` when an existing llama.cpp/OpenAI-compatible endpoint already serves `qwen3.6-27b-turbo3`; no Ollama pull is needed for that path.

## Optional local ASR mounts

`whisper-cpp-local` expects a user-managed `whisper.cpp` binary and GGML model. Mount them through `.env`:

```env
LOCAL_MODELS_DIR=./models
WHISPER_CPP_BIN_DIR=./third_party/whisper.cpp/build/bin
WHISPER_CPP_BINARY=/opt/whisper.cpp/bin/whisper-cli
WHISPER_CPP_MODEL_PATH=/models/ggml-large-v3-q5_0.bin
```

Then run:

```bash
docker compose --profile ai exec app \
  uv run python -m podcast_auto_editor transcribe input.wav \
    --provider whisper-cpp-local \
    --binary "$WHISPER_CPP_BINARY" \
    --model-path "$WHISPER_CPP_MODEL_PATH" \
    --language zh \
    --threads 8 \
    --out runs/transcript.json
```

## MiniMax fallback

`MINIMAX_API_KEY` is present only as an optional environment variable placeholder. The default compose stack does not call MiniMax and does not enable cloud behavior implicitly.

## Safety notes

- `ollama` is exposed only on localhost.
- `.env`, model files, generated `runs/`, and `.omx/` are ignored/local-only.
- GPU access is declared with Compose `deploy.resources.reservations.devices` using the NVIDIA driver and `gpu` capability.
