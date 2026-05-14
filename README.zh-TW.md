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

## 報告與介面

目前介面路線是：CLI → 靜態 HTML → 文字模式 review helper → 本機單人 UI → 可選桌面包裝。

靜態 HTML report：

```bash
uv run python -m podcast_auto_editor html-report runs/episode --out runs/episode/report.html
```

HTML report 會連到本機 preview、diff、recovery、export files，不會上傳資料，也不需要伺服器。

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

`review serve` 預設只綁定 `127.0.0.1`，決策會寫入與 CLI 相同的 `review-session.json`。
`review launcher` 會產生本機啟動檔，啟動同一個 localhost-only review server；這些 launcher 是本機 artifacts，不應提交進版控。

## AI 資源 profiles

預設 AI 規劃是單張 RTX 4090 的本機優先路徑：

```bash
uv run python -m podcast_auto_editor ai resources --format markdown
uv run python -m podcast_auto_editor ai resources --profile rtx4090-local --format json
```

`rtx4090-local` 是預設 profile，用於本機 ASR、本機 LLM reasoning 與 deterministic audio analysis。`minimax-fallback` 只記錄為明確指定時才使用的非本機備援；它需要 `MINIMAX_API_KEY`，且不會被隱式啟用。
