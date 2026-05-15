# 規劃：validate-run 預檢指令

日期：2026-05-15
分支：`feature/validate-run-command`

## 目標

新增 `validate-run` CLI 指令，在媒體處理前一起驗證 config、timeline 與可選 transcript。這補齊 roadmap 的 validation hardening 缺口，讓 transcript 超出媒體長度等跨檔案錯誤能在 `run`、`dry-run` 或 render 之前被攔下。

## 限制

- 重用現有 validator，不引入新的 schema dependency。
- 指令必須是 read-only，不寫 run artifacts 或 media exports。
- Config 驗證重用 `load_config` / `validate_config`。
- Timeline 驗證重用 `validate_timeline`。
- Transcript 驗證重用 `load_transcript_segments`，並在 timeline media duration 或明確 `--duration` 可用時做長度邊界檢查。
- 維持 `.omx` 不進版控，並用 uv 驗證。

## 驗收條件

- 有效 config + timeline + transcript 會 exit 0 並輸出簡短 OK summary。
- 無效 config 會 exit 1 並輸出可操作錯誤訊息。
- 無效 timeline 會 exit 1 並輸出 timeline validation errors。
- transcript cue 超過已知 media duration 時，會在寫任何 artifact 前 exit 1。
- 可以只驗證 config、只驗證 timeline、只驗證 transcript，或任意組合。
- README 與 README.zh-TW 文件化預檢指令。
