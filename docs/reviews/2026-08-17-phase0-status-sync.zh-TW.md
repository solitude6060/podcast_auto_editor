# 審查：`docs/2026-08-17-status-sync`

英文版：[`2026-08-17-phase0-status-sync.md`](2026-08-17-phase0-status-sync.md)

**日期：** 2026-08-17  
**範圍：** `dev` `2c9a81d` … `db56c26`  
**分支：** `docs/2026-08-17-status-sync`

## 這次進來的內容

| Commit | 內容 |
|---|---|
| `86d9560` | pyannote pipeline 沒有 `.to` 時略過 CUDA 搬移 |
| `08a165b` | two-pass loudnorm、有損輸出 true-peak 重試、各 profile 報告 |
| `21e68ba` | README／SDD／`user_todo`／2026-08-17 文件對齊 |
| `db56c26` | 寫入階段 0 hash |

## 做得好的地方

- CUDA 主機崩潰有強迫 `is_available` 的回歸測試。
- two-pass loudnorm 與有損 margin 重試有直接測試。
- MiniMax 金鑰只從環境變數讀，測試確認不會寫進草稿。
- README 比較表已含 `auto-editor`，`recipe.v1` 標成已實作，並寫明沒有降噪。

## 分級

| ID | 發現 | 嚴重度 | 這次修？ | 原因 |
|---|---|---|---|---|
| F1 | 後面的 profile 失敗時，頂層 `quality_gate_report` 仍是第一個 profile | 高 | 是 | 違反 2026-05-18 計畫「不要留下模稜兩可的部分成功」。Markdown 可能印 `Quality gate: True`，但 `podcast-stereo` 已失敗。 |
| F2 | 失敗時的 export metadata 只在記憶體裡 | 高 | 是 | `render`／`run` 遇到 `MediaToolError` 不會寫 `timeline.accepted.v1.json`。報告讀的是檔案，所以真正失敗時看不到新欄位。 |
| F3 | MiniMax 測試同一段 diff 刪掉了 `operation_explanations` 斷言 | 低 | 是 | 補回即可。 |
| F4 | loudnorm JSON 缺欄會丟 `KeyError` | 低 | 否 | 與既有 `measure_audio_quality` 同一寫法。 |
| F5 | SDD 品質門檻沒寫 two-pass／有損重試 | 中 | 是 | 規格與程式不一致；改文件。 |

## 結論

**要求修改。** 先修 F1、F2，再更新專案文件。
