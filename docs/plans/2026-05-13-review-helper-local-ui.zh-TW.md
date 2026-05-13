# 審閱輔助與本機介面完成增量

## 目標
完成介面路線圖中的剩餘 MVP 項目：提供本機優先的審閱輔助指令，以及最小可用的 localhost 審閱介面。兩者都寫入同一份 `review-session.json`，讓 CLI 與瀏覽器介面可以共用審閱狀態。

## 範圍
- UI-2：新增 `review next` 指令，顯示下一個需要製作人決策的操作，並提供可複製的 `review decide` 指令。
- UI-3：新增單人本機審閱伺服器，只使用 Python 標準函式庫；讀取 run artifacts，並把決策附加到 `review-session.json`。
- UI-4：以文件方式提供桌面包裝器準備度：先用本機 URL/啟動指令驗證流程，不在此階段加入正式桌面封裝，避免過早增加維護負擔。

## 驗收條件
- `podcast-auto-editor review next <session> --timeline <proposed>` 會回傳下一個尚未決策或已 undo 的操作，包含風險、信心分數、預覽、說明等欄位。
- `review next` 支援 JSON 與 Markdown 輸出。
- 本機審閱伺服器提供 GET 狀態/下一筆操作與 POST 決策處理，並沿用既有 `review_session.py` 邏輯。
- 本機伺服器預設只綁定 localhost，並拒絕非本機 host 值，除非未來另行規劃開放。
- 使用者文件具備繁體中文內容。
- `uv` 測試與 Python 編譯檢查全部通過。
