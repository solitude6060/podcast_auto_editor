# RTX 4090 本機優先 AI 資源 profiles

## 目標
把單張 RTX 4090 工作站的 AI 資源規劃寫成 repo-native profile，讓未來 ASR、LLM、音樂、影像 adapter 有安全預設：本機優先、符合 24GB VRAM，MiniMax 只作為明確指定的非本機備援。

## 範圍
- 新增 `rtx4090-local` 與 `minimax-fallback` AI resource profile 定義。
- 新增 CLI 指令，以 JSON 或 Markdown 查看 profiles。
- `rtx4090-local` 是預設 profile。
- MiniMax 標示為非本機、fallback-only，且不會被隱式啟用。
- 更新英文與繁體中文使用文件。

## 驗收條件
- `ai resources --format json` 會回傳所有 profiles 與預設 profile metadata。
- `rtx4090-local` 包含適合 24GB VRAM 的本機 ASR / LLM / music / image roles。
- `minimax-fallback` 標示 `local=false`、`fallback_only=true`，且不是預設。
- 未知 profile 名稱會清楚失敗。
- 不儲存 API keys、secrets 或 cloud credentials。
- `uv` 測試與 compileall 全部通過。
