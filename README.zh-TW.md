# Podcast Auto Editor

本專案是本機優先、CLI 優先的 podcast 後製工具。目標是自動處理完整單集的音訊，並保留可檢查、可回復的剪輯流程。

目前功能包含：
- 偵測長靜音並提出剪輯建議。
- 依 transcript 提出 speech cleanup / retake 建議。
- 產生 per-operation preview、diff、recovery map。
- 產生 transcript、SRT、VTT、chapters。
- 輸出 archive WAV、podcast stereo MP3、podcast mono MP3。
- 支援 review session，可記錄 accept / reject / undo 決策。
- 產生本機靜態 HTML report。

## 快速開始

```bash
uv sync --group dev
uv run python -m podcast_auto_editor probe input.wav --out runs
uv run python -m podcast_auto_editor run input.wav --out runs
uv run python -m podcast_auto_editor transcribe input.wav --provider stub --out transcript.json
uv run python -m podcast_auto_editor validate-run --timeline runs/input/timeline.proposed.v1.json --transcript-json transcript.json
uv run python -m podcast_auto_editor report runs/input --format markdown
uv run python -m podcast_auto_editor html-report runs/input --out runs/input/report.html
uv run python -m podcast_auto_editor project init my-show --name "My Show"
uv run python -m podcast_auto_editor batch dry-run ep1.wav ep2.wav --out runs
```

如果有安裝 FFmpeg / ffprobe，工具會進行真實媒體 probe、preview 與 render。純 timeline、review、report、validation 邏輯只使用 Python 標準庫與測試套件。

## 安全政策

Speech / retake 類剪輯預設只會是 `proposed`，不會自動接受。要接受 speech-changing edit，必須用人工審核流程或符合低風險自動接受規則。

人工接受範例：

```bash
uv run python -m podcast_auto_editor review-accept runs/episode/timeline.proposed.v1.json \
  --operation-id retake_abc123 \
  --reviewer producer \
  --note "Confirmed duplicate intro" \
  --out runs/episode/timeline.reviewed.v1.json
```

Review session 範例：

```bash
uv run python -m podcast_auto_editor review status runs/episode/review-session.json
uv run python -m podcast_auto_editor review decide runs/episode/review-session.json \
  --operation-id speech_abc123 \
  --decision accept \
  --reviewer producer
uv run python -m podcast_auto_editor review rebuild runs/episode/review-session.json \
  --timeline runs/episode/timeline.proposed.v1.json \
  --out runs/episode/timeline.accepted.v1.json
```

## Transcript 產生與匯入

可以用 `transcribe` 透過本機 provider 邊界產生 `transcript.v1` JSON：

```bash
uv run python -m podcast_auto_editor transcribe input.wav --provider stub --out transcript.json
```

內建的 `stub` provider 是 deterministic、無額外依賴，主要用於測試與流程串接。未來真實 ASR provider 應以 optional adapter 方式加入；provider 輸出會先通過 transcript validation，才會寫入檔案。

可用 `validate-run` 在媒體處理前做 read-only 預檢：

```bash
uv run python -m podcast_auto_editor validate-run \
  --config config.json \
  --timeline runs/episode/timeline.proposed.v1.json \
  --transcript-json transcript.json
```

如果 timeline media duration 或明確 `--duration` 可用，超出媒體長度的 transcript cue 會在寫任何 run artifact 前被拒絕。

## 報告與介面

目前介面路線是：CLI → 靜態 HTML → 文字模式 review helper → 本機單人 UI → 可選桌面包裝。

靜態 HTML report：

```bash
uv run python -m podcast_auto_editor html-report runs/episode --out runs/episode/report.html
```

HTML report 會連到本機 preview、diff、recovery、export files，不會上傳資料，也不需要伺服器。

## AI 輔助與可解釋性

可用 `ai draft` 由 timeline + transcript 產生「僅供 review」的建議草稿：

```bash
uv run python -m podcast_auto_editor ai draft \
  --timeline runs/episode/timeline.proposed.v1.json \
  --transcript-json runs/episode/transcript.json \
  --dry-prompt \
  --format json
```

草稿預設會寫到 timeline 目錄下的 `ai/ai-draft.v1.json`。

`--dry-run` 為 `--dry-prompt` 的別名（同時視為 `--no-net`），適合離線或 CI 安全流程。

可對單筆操作做 AI 解釋：

```bash
uv run python -m podcast_auto_editor explain runs/episode/timeline.proposed.v1.json \
  --operation-id speech_abc123 \
  --with-ai \
  --transcript-json runs/episode/transcript.json \
  --dry-prompt \
  --format json
```

在 `--dry-prompt` 或 `--dry-run` 模式下，不會觸發任何網路 AI 呼叫。

## Docker AI stack E2E 檢查

可用下列 script 跑本機 AI stack 檢查：

```bash
./scripts/e2e-docker-ai-stack.sh --dry-run
./scripts/e2e-docker-ai-stack.sh
```

腳本會啟動 Compose 的 app + ollama（若可用）、執行一次簡易 smoke CLI、最後做清理關停。

## 專案與批次 dry-run

用 `project init` 建立 `.omx` 之外的本機專案 manifest：

```bash
uv run python -m podcast_auto_editor project init my-show --name "My Show"
```

用 `batch dry-run` 檢查多集節目，但不輸出 edited media exports：

```bash
uv run python -m podcast_auto_editor batch dry-run ep1.wav ep2.wav --out runs
```

指令會輸出 `runs/batch/batch-report.json` 與 `runs/batch/batch-report.md`。單集失敗時預設會記錄錯誤並繼續處理後續集數；若需要第一個失敗就停止，可加上 `--fail-fast`。

## 開發驗證

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests
./scripts/smoke.sh
```

GitHub Actions 會跑同一組 uv 測試與 compileall。`.omx/`、`.venv/`、runs、credentials、cache 都不能進版控。

### 本機審稿介面

產生 run directory 後，可以使用 scriptable review helper 或本機 review server：

```bash
uv run python -m podcast_auto_editor review next runs/episode/review-session.json   --timeline runs/episode/timeline.proposed.v1.json
uv run python -m podcast_auto_editor review serve runs/episode
uv run python -m podcast_auto_editor review launcher runs/episode --out runs/episode/open-review-ui.sh --desktop-out runs/episode/open-review-ui.desktop
```

`review serve` 預設只綁定 `127.0.0.1`，決策會寫入與 CLI 相同的 `review-session.json`。同時提供 Run Dashboard（待決策狀態、下一筆操作、AI draft 連結）。
`review launcher` 會產生本機啟動檔，啟動同一個 localhost-only review server；這些 launcher 是本機 artifacts，不應提交進版控。

## Docker Compose 本機 AI stack

若要容器化本機開發與可選 RTX 4090 AI service，請看 [`docs/docker-compose-ai-stack.zh-TW.md`](docs/docker-compose-ai-stack.zh-TW.md)：

```bash
cp .env.example .env
docker compose --profile ai up -d ollama app
docker compose --profile ai exec app uv run --group dev pytest -q -p no:cacheprovider
```

Compose stack 會讓 `ollama` 只綁定 localhost，使用 NVIDIA GPU reservation 給本機 AI service，並讓 model files、`.env`、generated runs 與 `.omx` 維持在版本控制之外。

檢查本機 AI wiring，但不下載模型：

```bash
uv run python -m podcast_auto_editor ai doctor --optional-whisper --format markdown
docker compose --profile ai exec app uv run python -m podcast_auto_editor ai doctor --optional-whisper
```

如果目前有其他專案正在使用 GPU，請維持檢查輕量：用 `--no-ollama` 跳過 live Ollama probe；模型下載改在確認的維護時段手動進行；正式載入 30B 等級本機 LLM 前，先用較小 smoke model 測試。

檢視本機模型目錄並列出手動 pull 指令；這不會執行下載：

```bash
uv run python -m podcast_auto_editor ai models --format markdown
uv run python -m podcast_auto_editor ai models --tier api-local --pull-plan
uv run python -m podcast_auto_editor ai models --tier smoke --pull-plan
LOCAL_LLM_BASE_URL=http://127.0.0.1:9090/v1 \
  uv run python -m podcast_auto_editor ai models --readiness --tier api-local --no-ollama
```

`api-local` 是給既有 llama.cpp / OpenAI-compatible API 模型使用，例如 `qwen3.6-27b-turbo3`；它不會輸出下載指令，只會在 readiness 檢查時讀 `/v1/models`。

## AI 資源 profiles

預設 AI 規劃是單張 RTX 4090 的本機優先路徑：

```bash
uv run python -m podcast_auto_editor ai resources --format markdown
uv run python -m podcast_auto_editor ai resources --profile rtx4090-local --format json
```

`rtx4090-local` 是預設 profile，用於本機 ASR、本機 LLM reasoning 與 deterministic audio analysis。`minimax-fallback` 只記錄為明確指定時才使用的非本機備援；它需要 `MINIMAX_API_KEY`，且不會被隱式啟用。

### Optional faster-whisper 本機 ASR

若使用 RTX 4090 profile，可在本機環境自行安裝 optional ASR dependencies，並明確指定 `faster-whisper-local`：

```bash
uv run python -m podcast_auto_editor transcribe input.wav \
  --provider faster-whisper-local \
  --model large-v3 \
  --device cuda \
  --compute-type float16 \
  --out transcript.json
```

`faster-whisper-local` 不是 core dependency。若沒有安裝 `faster_whisper`，指令會在寫入 `transcript.json` 前失敗。Deterministic `stub` provider 仍是測試與無依賴 smoke check 的預設。

### Optional whisper.cpp 本機 ASR

`whisper-cpp-local` 是較低 Python 依賴的本機備援 provider，適合自行管理 `whisper.cpp` build 與 GGML model 檔案的環境：

```bash
uv run python -m podcast_auto_editor transcribe input.wav \
  --provider whisper-cpp-local \
  --binary /path/to/whisper-cli \
  --model-path /models/ggml-large-v3-q5_0.bin \
  --language zh \
  --threads 8 \
  --out transcript.json
```

此 provider 必須明確提供本機 binary 與 model path，並以 JSON 輸出模式執行 `whisper.cpp`。若 binary/model 不存在、外部指令失敗、JSON 無效，或 transcript segment 不合法，會在寫入 `transcript.json` 前失敗。
