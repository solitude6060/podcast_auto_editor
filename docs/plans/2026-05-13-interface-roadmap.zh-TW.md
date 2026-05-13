# Podcast Auto Editor 介面路線圖

## 目標
在 CLI MVP 之後，逐步加入更好用的本機介面，同時保留安全審稿、可回復時間線，以及不上雲的限制。

## 原則
- 本機優先：除非之後明確要求，不做雲端協作、不做上傳或發布整合。
- 審稿優先：每個高風險剪輯都要能透過 operation preview、explanation、diff、recovery artifact 檢查。
- CLI 仍是穩定自動化介面；所有 UI 都讀同一批 run artifacts，不另外發明一套流程。
- 先做靜態、離線介面，再做互動式介面。

## 介面階段

### UI-1 — 靜態 HTML 報告強化
目前已有 `podcast-auto-editor html-report`。
後續改進：
- 依 proposed / accepted / rejected 過濾 operation。
- 顯示 risk 與 detector 摘要。
- 連到 operation explanation 與 review-session status。
- 對「需要人工審核」與「安全預設」加上明確樣式。

驗收：
- HTML 仍是靜態、本機檔案。
- 連結維持 run directory 內相對路徑。
- 測試涵蓋 escaping 與本機 artifact link。

### UI-2 — 文字模式審稿輔助
在 review session 上做 terminal-friendly 的審稿流程。
可能指令：

```bash
podcast-auto-editor review next runs/ep1/review-session.json --timeline runs/ep1/timeline.proposed.v1.json
podcast-auto-editor review decide ...
podcast-auto-editor review rebuild ...
```

驗收：
- 不需要互動式依賴，也能用腳本執行。
- 輸出永遠包含 operation id、risk、confidence、preview refs、explanation fields，以及下一步 decision command。

### UI-3 — 本機單人 Web 介面
建立只讀取 run directory、只寫 review-session JSON 的本機 UI。
建議架構：
- 後端：Python 標準庫 `http.server`，或之後有必要才加入極小本機 adapter。
- 前端：靜態 HTML/JS 讀取 JSON artifacts。
- 狀態：只寫 `review-session.json` 與重建後的 timeline。

驗收：
- 只在 localhost 執行。
- 不做帳號、雲端同步、發布整合。
- 可直接操作既有 run directory。
- 使用同一個 `review_session.py` replay 邏輯。

### UI-4 — 可選桌面包裝
只有在本機 Web UI 已經足夠好用後才考慮：
- 包成桌面捷徑或 wrapper。
- CLI 與 artifact 格式仍是權威來源。

## 依賴
- A2 per-operation preview refs。
- A4 explainability data。
- A6 review-session state machine。
- A7 static HTML report。

## 驗證
- Artifact parsing 與 HTML/JSON 產生的單元測試。
- 使用 generated run artifacts 的端到端 fixture。
- HTML escaping 與 path traversal 防護測試。
