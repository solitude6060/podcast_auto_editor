# 規劃：Docker Compose 本機 AI stack

日期：2026-05-15
分支：`feature/validate-run-command`

## 目標

新增 Docker Compose 開發/執行 stack，可啟動 podcast editor app 與本機 RTX 4090 AI service，同時不把 cloud API 或 model 檔案納入 repository。

## 限制

- 預設維持本機優先、不使用 cloud。
- 本機 LLM service 使用 Docker Compose GPU reservation。
- MiniMax 只作為環境變數設定的備援，不提交 key value。
- 不提交 model weights、generated runs、`.omx` 或 credentials。
- App dependency 維持 uv 管理。
- `whisper.cpp` 與 GGML models 由使用者以 volume mount 提供，不放進 image。

## Compose services

- `app`：`podcast_auto_editor` 的本機開發/執行 container，包含 uv、source mount、run artifacts 與 optional model mounts。
- `ollama`：RTX 4090 workflow 可選的本機 GPU LLM service，只綁定 localhost。

## 驗收條件

- `compose.yaml` 定義 app 與本機 AI service，且 NVIDIA GPU reservation 存在。
- `.env.example` 文件化安全的本機變數，不含 secrets。
- Dockerfile 使用 uv 且不 vendor models。
- Docker 文件有英文與繁中版本。
- 測試可在不需要 Docker daemon 的情況下驗證 compose safety constraints。
