# 規劃：AI 模型 readiness report

日期：2026-05-15
分支：`feature/ai-model-readiness`

## 目標

新增輕量 `ai models --readiness` 模式，把本機 model catalog 和 Ollama `/api/tags` 回應比對，讓使用者知道 smoke/recommended/heavy models 哪些已安裝；不下載模型、不跑 GPU inference。

## 限制

- 只讀：不下載模型、不推論。
- Ollama request 有 timeout；offline 模式可用已保存 tags JSON fixture。
- GPU 被其他專案共享時仍能用 smoke tier 做檢查。
- 支援 JSON 與 Markdown output。
- 更新繁中使用者文件。

## 驗收條件

- Readiness report 列出 catalog models，並標示 `installed` true/false。
- Offline `--ollama-tags-json` 不需要網路或 Docker。
- Live `--ollama-url` 有 timeout，連線失敗回報 warning。
- CLI 對 reachable/offline report exit 0；missing models 不算 process error。
