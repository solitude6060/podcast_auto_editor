# Podcast Auto Editor — 專案現況檢視

英文版：[`2026-08-17-project-status-review.md`](2026-08-17-project-status-review.md)

**檢視日期：** 2026-08-17  
**分支：** `dev`，`2c9a81d`（2026-05-18 20:07 +0800，合併 PR #48）  
**工作區：** 有未提交變更（17 個已追蹤檔，+383/−15），另有未追蹤的 `.claude/`、`.omc/`、2026-05-18 podcaster-ready 文件  
**距上次 commit：** 至 2026-08-17 為 91 天

**當日階段 0 補記：** 衛生工作落在 `docs/2026-08-17-status-sync`。README 已改為 `recipe.v1` 已實作，且 pyannote 在可選套件齊備時可跑。2026-05-18 音量／報告修改為 `f70f7ac`。CUDA `.to` 防護為 `d02b1b8`。該批未提交 diff 已不再是現況。新增回歸測試後收集數為 325（本機 314 passed、11 skipped）。

---

## 1. 進度

```
命令列契約          已完成
timeline.v1 / 還原  已完成
dry-run + 報告      已完成
本機審核 UI         已完成（只綁 127.0.0.1）
recipe.v1           已完成（README 仍寫 planned）
ASR 適配            已完成（預設仍是 stub）
pyannote 適配       已完成（README 仍寫後續 PR）
真實集數證據        未完成（walkthrough 用 stub；音檔碟未掛上）
1.0 發布            自 2026-05-18 卡在簽核；不建議現在做
```

2026-05 中旬 Persona Stage 1 的 A–H 與 X1–X4.1 已進 `dev`。缺的不是再多一個 provider，而是一集真實音檔走完「真實語音辨識 → 人工審核 → 通過音量閘門的匯出」。

---

## 2. 程式統計（2026-08-17，含未提交變更的工作區）

| 指標 | 數值 |
|---|---|
| 套件模組 | 27 個 `.py` |
| 原始碼行數 | 6,141 |
| 測試檔 | 36 |
| 測試行數 | 6,642 |
| 收集到的測試 | 324 |
| 已追蹤 Markdown | 161 |
| `dev` 領先 `main` | 40 個 commit |
| 鎖定中的 worktree | 19 個，位於 `.claude/worktrees/` |

`cli.py` 為 1,092 行，是最大的模組。

---

## 3. 已存在的能力

核心：`timeline.v1`、安全政策（改語音的剪輯預設 proposed）、ffmpeg 靜音偵測、filler / retake / backchannel 啟發式、WAV/MP3 匯出與 LUFS／true-peak 閘門、`recipe export/apply`。

介面：命令列、靜態 HTML 報告、文字審核、localhost 審核頁。桌面包裝只有 launcher，沒有獨立應用程式。

AI：ASR / 說話人分離 / 對齊都有 mock 與真實適配；quickstart 預設 stub + dry-prompt。`run_pipeline` 寫出的 `exports/transcript.json` 仍是 `"source": "post-edit-stub"`（`pipeline.py:438-448`）。

---

## 4. 規格與程式不一致

- README 對照表把 recipe 標成 planned，程式已實作。
- README 仍寫「之後再加真實 ASR」「pyannote 後續 PR」，`dev` 上都已有。
- SDD 寫 29 個測試通過；今日收集到 324。
- 2026-05-17 競品表把本工具的降噪標成有 RNNoise/Demucs；原始碼沒有降噪。

---

## 5. 目前阻擋決策的項目

1. **證據：** 還沒有一集真實口語走過真實 ASR → 審核 → 可發布匯出。PR-A 用 4 秒合成靜音。PR-A2 的 `--real-audio` 仍用 stub 逐字稿。walkthrough 指定的外接碟路徑今日未掛上。
2. **未提交變更：** 2026-05-18 的音量／報告修改還在工作區，clean checkout 會消失。
3. **文件落後：** README / SDD / 對照表與 `dev` 不符，也沒有 `auto-editor`。
4. **`main` 落後 40 個 commit：** 這是發布流程停住，不是功能沒做。
5. **可延後：** Lattifai decode、審核 UI 上一筆、macOS/WSL CI。

---

## 6. 建議立刻做的事

1. 在真實集數可發布或寫下失敗紀錄之前，不要標 `1.0.0`。
2. 決定 2026-05-18 未提交修改要收成功能分支，還是審查後丟棄。
3. 把 README / SDD / 對照表對齊 `dev` 與 `docs/research/2026-08-17-competitor-landscape.md`。
4. 用非 stub 的 ASR 跑一集華語真實音檔，寫 `docs/fix-logs/2026-08-XX-real-episode.md`。
5. 依該紀錄只加深一條：審核 UX、響度，或中文 ASR 品質。

後續計畫：`docs/plans/2026-08-17-adjustment-and-next.md`。
