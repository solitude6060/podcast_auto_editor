# 變更紀錄

本文件記錄重要使用者可見變更。

## 尚未發布

### 新增
- 本機優先 podcast auto-editor MVP。
- 可回復 timeline、preview、diff、recovery artifacts。
- transcript、subtitle、chapter 輸出。
- export profiles：archive WAV、podcast stereo MP3、podcast mono MP3。
- review session：accept / reject / undo 決策可 replay。
- 靜態 HTML report。
- GitHub Actions 使用 uv 跑 pytest 與 compileall。
- 新增 `podcast_auto_editor ai draft`：以 timeline + transcript 產生 review-only `ai/ai-draft.v1.json`，並支援 `--dry-prompt` / `--dry-run` 離線輸出。
- `podcast_auto_editor explain --with-ai` 新增 AI 解釋欄位（含 `ai_explanation`），並支援 `--dry-prompt` 安全模式。
- `review serve` dashboard 整合 AI 草稿連結與 artifacts/context（API + HTML）資訊。
- 新增本機 AI stack e2e 腳本：`scripts/e2e-docker-ai-stack.sh` 及對應腳本測試。

### 變更
- 尚未正式發布；發布前需更新版本與驗證結果。

### 修正
- 尚未正式發布。
- `ai draft` 加入 `--dry-run` 互斥/別名行為，並對齊 `--no-net` 安全路徑。
- `review serve` 在含 AI 草稿時會保留對 dashboard 的可見連結，避免 API/HTML 資訊斷層。
