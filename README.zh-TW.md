# Podcast Auto Editor

English version: [`README.md`](README.md)

## 為什麼做這個

- **整個流程都在你的筆電上跑。** 不用註冊、不用登入、不用上傳。音檔不會離開你的硬碟。
- **完全免費，沒有月費，沒有按分鐘計費。** 三月剪 90 分鐘那集，四月休息，五月剪兩集 — 不管怎麼用，成本都是零。
- **每個剪輯動作都可以審過再上線。** 工具產出一份 `timeline.v1` JSON 列出所有提議的剪輯，加上每段剪輯的試聽檔；你在本機 dashboard 上一個一個按 accept 或 reject。沒有任何 AI 自動幫你改掉的事。
- **剪輯紀錄是可重現的。** 一次跑完會產一份可以 commit 進 git 的紀錄檔，幾個月後對同一份原始音檔 replay 就會得到一模一樣的成果。`docs/research/2026-05-17-competitor-landscape.md` 裡調查過的競品都沒做這件事。

## 怎麼跟其他工具比

| | Descript | Riverside | Cleanvoice | Podcast Auto Editor |
|---|---|---|---|---|
| 在本機跑 | 不是 | 不是 | 不是 | **是** |
| 音檔要上傳給廠商 | 要 | 要 | 要 | **不用** |
| 月費 | 16–50 美金 | 24–79 美金 | 11–90 美金 | **免費** |
| 按 AI 用量計費 | 要（按分鐘） | 要 | 要（按小時） | **不用** |
| 一個一個審剪輯動作 | 部分 | 部分 | 只有報告 | **可以** |
| 剪輯紀錄可以丟進 git | 不行 | 不行 | 不行 | **可以**（規劃中，見 roadmap） |

資料來源：`docs/research/2026-05-17-competitor-landscape.md`（2025-2026 各家定價頁 + Reddit / G2 用戶抱怨）。

## 這是什麼

一個跑在你筆電上的 podcast 後製流水線。用 canonical 可回復的 `timeline.v1` 在動媒體前就把剪輯記錄起來，主打音訊（WAV / MP3 / M4A），可選擇處理 MP4 同步 / 輸出，所有自動剪輯都透過 preview、diff、recovery 三種紀錄保留下來給你檢查。

具體功能：
- 偵測長靜音，提議要剪掉的時間點（只有確定的靜音會自動接受，會改動語意的剪輯一律要人工審）。
- 產生 transcript、字幕（SRT / VTT）、章節標記。
- 草擬 AI 章節 / 摘要 / show notes（只是建議，絕對不會自動套用；用 `--dry-prompt` 可以不連網）。
- 輸出 archive WAV 加上 podcast stereo / mono MP3，每個輸出都有 LUFS 跟 true-peak 品質檢查。
- 產出 `timeline.v1` 跟 recovery map，所有接受的剪輯都可以回復。

## 這不是什麼

- **不是 DAW 替代品。** 多軌混音、效果器、創意剪輯還是該用 Reaper / Hindenburg / Audacity。
- **不是雲端錄音工具。** 多人遠端錄音請繼續用 Riverside / SquadCast / Zencastr，然後把檔案匯進這裡處理。
- **不是聲音克隆工具。** 故意不做合成聲音。
- **不是發布工具。** RSS / Spotify / Apple 上架請用其他工具。

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

## Diarization 講者分離（可選）

工具可以幫每個 transcript cue 標上 `speaker_id`（哪個人講的），讓 AI 章節草稿、show notes、per-speaker filler 偵測都能正確歸屬。Provider 介面是可換的：

- **`mock`**（離線、內建）— 讀一份 JSON config 把預期 segments 直接回傳。CI 跟沒有 HuggingFace token 的開發機都用這個。
- **`pyannote`** — 用 lazy import 包裝 `pyannote-audio` 3.x。實機整合留到後續 PR；現在跑會丟一個清楚的 `DiarizationProviderError`，訊息會告訴你是要先 `uv add pyannote-audio` 還是等實機整合 PR 落地。

```bash
# Mock provider — 從 JSON config 讀 segments（離線）
uv run python -m podcast_auto_editor diarize input.wav \
  --provider mock \
  --config diarization-config.json \
  --out runs/episode/speaker_segments.v1.json

# Pyannote provider — 需要 `uv add pyannote-audio` 跟 HF_TOKEN
uv run python -m podcast_auto_editor diarize input.wav \
  --provider pyannote \
  --out runs/episode/speaker_segments.v1.json
```

Mock config 格式（`diarization-config.json`）：

```json
{
  "segments": [
    {"start": 0.0,  "end": 12.5, "speaker_id": "spk0", "confidence": 0.95},
    {"start": 12.5, "end": 30.0, "speaker_id": "spk1", "confidence": 0.92}
  ]
}
```

輸出（`speaker_segments.v1.json`）：`{schema_version, audio_path, segments: [{start, end, speaker_id, confidence}, ...]}`。JSON 用 sorted-keys + indent=2，git diff 友善。`transcript.v1` cue 可以選擇性帶 `speaker_id` 欄位，沒帶的舊 transcript 一樣會 validate。

## 可重現的剪輯紀錄（`recipe export` / `recipe apply`）

可以把整個 run 目錄打包成一份可攜帶的 `recipe.v1.json`，內容包含原始音檔的 sha256、accepted timeline、config 快照、以及（如果有的話）AI 草稿。把 recipe 提交進 git，幾個月後對同一份原始音檔 replay 一次，就會得到一模一樣的剪輯成果。

```bash
uv run python -m podcast_auto_editor recipe export \
  --run runs/episode \
  --out runs/episode/recipe.v1.json

uv run python -m podcast_auto_editor recipe apply \
  --recipe runs/episode/recipe.v1.json \
  --media source-episode.wav \
  --out runs/episode-replayed
```

`apply` 會用 recipe 裡的 sha256 驗證來源音檔，不符會直接拒絕。如果你真的要對重新編碼過或被修改過的音檔套用同一份 recipe，加上 `--allow-media-drift` — 新產生的 manifest 會記錄這個覆寫動作。

Recipe 本身不會把音檔內容塞進去，只記路徑、sha256、跟長度。Accepted timeline 是直接內嵌的，所以 recipe 是自給自足的。

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
