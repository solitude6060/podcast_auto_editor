# 規劃：AI 環境 doctor

日期：2026-05-15
分支：`feature/ai-env-doctor`

## 目標

新增 read-only `ai doctor` 指令，讓使用者在 Docker Compose stack 建立後，可以檢查本機 RTX 4090 AI 環境。指令會安全回報 Docker Compose 檔案、可選 Ollama 連線、可選 `whisper.cpp` binary/model path，以及 MiniMax fallback 設定，不洩漏 secret。

## 限制

- 只做 read-only 診斷；不下載模型，不呼叫非本機 API。
- MiniMax 仍是 fallback-only，secret value 必須 redacted。
- 只使用 Python 標準庫。
- 即使沒有 Docker daemon 也能使用；Compose 檔案檢查採靜態檢查。
- 需支援 JSON 與 Markdown output。
- 更新繁中使用者文件。

## 驗收條件

- 回報 `ok`、`warning` 或 `missing` checks，並提供可操作訊息。
- 靜態 Compose check 會確認本機 AI service 與 GPU reservation 線索。
- Ollama check 是可選且有 timeout。
- whisper.cpp binary/model checks 是可選 path existence checks。
- MiniMax check 只回報 env var 是否設定，不印出值。
- 所有 checks 為 ok/warning 時 exit 0；必要本機 artifact missing 時 exit 1。
