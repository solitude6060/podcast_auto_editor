# 專案與批次 dry-run 工作流

## 目標
實作進階路線圖 Phase A1：支援本機專案 manifest 與多集 podcast 的批次 dry-run 報告，不加入雲端協作、發布或上傳功能。

## 範圍
- 新增 `project init <project_dir>`，在 `.omx` 之外建立本機 `podcast-project.v1.json` manifest。
- 新增 `batch dry-run <inputs...>`，針對多個輸入檔執行可檢查的 dry-run。
- 單集失敗時預設繼續處理其他集數；只有在 `--fail-fast` 時才提前停止。
- 輸出 aggregate JSON 與 Markdown 報告，包含每集狀態、警告、移除總長與品質狀態。

## 驗收條件
- 批次 dry-run 不寫入 edited media exports，沿用既有 dry-run artifact 流程。
- 失敗集數會記錄在 aggregate report，不會阻止後續集數，除非使用 `--fail-fast`。
- Aggregate report 同時提供 JSON 與 Markdown。
- 使用者 README 文件具備繁體中文說明。
- `uv` 測試與 compileall 全部通過。
