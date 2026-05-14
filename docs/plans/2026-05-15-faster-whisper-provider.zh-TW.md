# Optional faster-whisper 本機 ASR provider

## 目標
實作第一個真正面向 RTX 4090 的本機 ASR adapter，同時保留 core zero-dependency：只有在使用者自行安裝 optional `faster_whisper` 套件與本機模型時，才可使用 `faster-whisper-local`。

## 範圍
- 新增 `FasterWhisperLocalProvider`，使用 optional import。
- 註冊 provider name `faster-whisper-local`，與 `stub` 並存。
- 新增 CLI 選項：ASR model、device、compute type。
- `stub` 仍是測試用 deterministic default；不把 faster-whisper 加進 `pyproject.toml` mandatory dependencies。
- 所有 provider 輸出都要先驗證成 `transcript.v1` 才能寫檔。
- 更新英文與繁體中文文件，記錄 4090 建議設定。

## 驗收條件
- 缺少 `faster_whisper` dependency 時清楚失敗，且不寫 output。
- Mocked faster-whisper module 可產生 normalized transcript segments。
- CLI 會把 `--model`、`--device`、`--compute-type` 傳給 provider。
- 未安裝 faster-whisper 時 core full test suite 仍通過。
- MiniMax 維持 fallback-only，不參與預設 ASR 選擇。
