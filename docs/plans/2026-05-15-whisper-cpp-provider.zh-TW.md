# 規劃：可選的 whisper.cpp 本機 ASR provider

日期：2026-05-15
分支：`feature/whisper-cpp-provider`

## 目標

新增可選的 `whisper-cpp-local` transcript provider，讓 RTX 4090 本機優先 profile 具備較低 Python 依賴的 ASR 備援路徑，可使用使用者自行管理的 `whisper.cpp` 執行檔與 GGML model。

## 限制

- `stub` 仍是測試與 smoke check 的 deterministic 預設 provider。
- 不把 `whisper.cpp` 或 model 檔案加入 Python dependency 或 repo artifact。
- 執行前必須明確提供本機 `--binary` 與 `--model-path`。
- provider 輸出必須先通過 `transcript.v1` 驗證，才可寫出 transcript 檔案。
- MiniMax 只維持非本機備援文件選項，不作為隱式 ASR runtime dependency。
- 保持 uv 驗證流程與 `.omx` 不進版控。

## CLI 契約

```bash
uv run python -m podcast_auto_editor transcribe input.wav \
  --provider whisper-cpp-local \
  --binary /path/to/whisper-cli \
  --model-path /models/ggml-large-v3-q5_0.bin \
  --language zh \
  --threads 8 \
  --out transcript.json
```

## 驗收條件

- `provider_names()` 包含 `whisper-cpp-local`。
- 缺少 `--binary` 或 `--model-path` 時清楚失敗，且不寫出檔案。
- 本機檔案不存在時，在執行外部程式前清楚失敗。
- 有效的 `whisper.cpp` JSON 輸出會轉成正規化 transcript segments。
- 無效 JSON 或無效 segment shape 會清楚失敗，且不寫出檔案。
- CLI 會傳遞 `--binary`、`--model-path`、`--language`、`--threads` 給 provider。
- README 與 README.zh-TW 都文件化可選用法。
- targeted 與 full uv test suites 都通過。
