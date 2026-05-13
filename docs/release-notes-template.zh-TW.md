# Release notes 範本

## 版本
`vX.Y.Z` — YYYY-MM-DD

## 重點
- （填寫本次版本重點）

## 使用者可見變更
- （填寫使用者可見變更）

## 相容性說明
- Timeline schema：
- Config schema：
- CLI 相容性：

## 驗證
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider`
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests`
- 若本機有 FFmpeg，執行 optional media smoke。

## 發布檢查
- [ ] `CHANGELOG.md` 與 `CHANGELOG.zh-TW.md` 已更新
- [ ] 版本 / tag 已決定
- [ ] `.omx/` 與 generated run artifacts 未被追蹤
- [ ] 沒有 secrets 或 cloud credentials
- [ ] 已記錄已知限制
