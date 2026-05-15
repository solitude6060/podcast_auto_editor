# Docker Compose 本機 AI Stack

本 repo 內建本機優先 Docker Compose stack，可用於開發、smoke tests，以及可選的 RTX 4090 AI service。

## Services

- `app`：`podcast_auto_editor` 的 Python/uv 開發 container。
- `ollama`：可選的本機 GPU LLM service，只綁定 `127.0.0.1:11434`。

這個 stack 不會把 model weights、credentials、generated runs 或 `.omx` state 放進版本控制。

## 前置需求

- Docker Engine 與 Compose v2。
- Host 需安裝 NVIDIA driver 與 NVIDIA Container Toolkit 才能使用 GPU。
- `ollama` profile 建議使用 RTX 4090 或相容 NVIDIA GPU。

## 啟動本機 AI stack

```bash
cp .env.example .env
mkdir -p runs models third_party/whisper.cpp/build/bin
docker compose --profile ai up -d ollama app
```

在 app container 內跑測試：

```bash
docker compose --profile ai exec app \
  uv run --group dev pytest -q -p no:cacheprovider
```

執行 CLI：

```bash
docker compose --profile ai exec app \
  uv run python -m podcast_auto_editor ai resources --format markdown
```

執行輕量 AI 環境 doctor：

```bash
docker compose --profile ai exec app \
  uv run python -m podcast_auto_editor ai doctor --optional-whisper --format markdown
```

如果其他專案正在使用 GPU，避免重型 probe：

```bash
uv run python -m podcast_auto_editor ai doctor --no-ollama --optional-whisper
```

模型下載刻意設計成手動操作。請先拉小型 smoke model，等 GPU 記憶體可用時再排程大型 model：

```bash
uv run python -m podcast_auto_editor ai models --tier smoke --pull-plan
docker compose --profile ai exec ollama ollama pull qwen3:0.6b
# 之後 GPU 資源可用時：
# docker compose --profile ai exec ollama ollama pull qwen3:32b
```

## 可選本機 ASR mounts

`whisper-cpp-local` 需要使用者自行管理的 `whisper.cpp` binary 與 GGML model。可透過 `.env` 掛載：

```env
LOCAL_MODELS_DIR=./models
WHISPER_CPP_BIN_DIR=./third_party/whisper.cpp/build/bin
WHISPER_CPP_BINARY=/opt/whisper.cpp/bin/whisper-cli
WHISPER_CPP_MODEL_PATH=/models/ggml-large-v3-q5_0.bin
```

執行範例：

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

## MiniMax 備援

`MINIMAX_API_KEY` 只是可選環境變數 placeholder。預設 compose stack 不會呼叫 MiniMax，也不會隱式啟用 cloud 行為。

## 安全注意事項

- `ollama` 只開在 localhost。
- `.env`、model files、generated `runs/` 與 `.omx/` 都維持 local-only。
- GPU access 使用 Compose `deploy.resources.reservations.devices`，指定 NVIDIA driver 與 `gpu` capability。
