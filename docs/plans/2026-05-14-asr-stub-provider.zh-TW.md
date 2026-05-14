# 可選本機 ASR adapter stub

## 目標
實作進階路線圖 Phase A3：建立不依賴雲端與必裝 ASR 套件的 transcript provider 邊界，並提供 deterministic stub provider，讓 transcript 產生流程可以被測試與串接。

## 範圍
- 新增 `podcast_auto_editor/asr.py`，定義 transcript provider protocol 與 provider registry。
- 新增 `transcribe <input> --provider stub --out <transcript.json>` CLI 指令。
- Provider 輸出必須經過既有 transcript validation 後才寫檔。
- Provider 失敗時不可寫入輸出檔，也不可修改媒體 artifacts。
- 更新英文與繁體中文使用文件。

## 驗收條件
- Core tests 不需要 ASR 依賴也會通過。
- Stub provider 會寫出 normalized `transcript.v1` JSON。
- 無效 provider 輸出會清楚失敗，且不寫入 output file。
- 未知 provider 會回報可操作的 CLI 錯誤訊息。
