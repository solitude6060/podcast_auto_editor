# 規劃：AI 模型目錄與下載計畫

日期：2026-05-15
分支：`feature/ai-model-plan`

## 目標

新增本機 AI model catalog 與 `ai models` CLI，讓使用者可以檢視安全模型等級並產生明確 Ollama pull 指令，但不自動下載大型模型，也不消耗 GPU 資源。

## 限制

- 測試、CI、預設 CLI output 都不能自動下載模型。
- 模型下載指令只以文字輸出，除非使用者之後手動執行。
- 支援 `smoke` tier，供其他專案正在使用 GPU 時做低資源驗證。
- 30B 等級模型標示為 heavy/manual，不適合同時共享 GPU 使用。
- MiniMax 維持非本機備援文件選項。
- 只使用 Python 標準庫。
- 使用者文件需要繁中版本。

## 驗收條件

- Catalog 包含 smoke、recommended、heavy/manual tiers。
- JSON output 可 script，且包含 pull command strings。
- Markdown output 會提醒 GPU sharing 與手動下載時段。
- Pull plan output 不會執行 `ollama pull`。
- 測試驗證 planner 不會執行 shell command。
