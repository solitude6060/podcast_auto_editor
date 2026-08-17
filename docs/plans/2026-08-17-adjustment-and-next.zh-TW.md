# 調整方向與後續計畫

英文版：[`2026-08-17-adjustment-and-next.md`](2026-08-17-adjustment-and-next.md)

日期：2026-08-17  
本文件只定方向，不含實作。

**階段 0 狀態（2026-08-17）：** 已落在 `docs/2026-08-17-status-sync`：`86d9560`、`08a165b`、`21e68ba`、`db56c26`。審查見 `docs/reviews/2026-08-17-phase0-status-sync.zh-TW.md`；F1／F2 已在同分支修好。19 個鎖住的 worktree 未動。沒有改版本號。沒有 `dev` → `main`。沒有 push／開 PR。

---

## 第一性原理（結論）

使用者要的是「要不要繼續、往哪調」。`user_todo.md` 留下的 1.0 簽核與更多 provider，解決不了這個問題。能改寫決策的是一集真實口語：真實語音辨識 → 人工審核 → 通過或明確失敗的發布匯出。

已核對：recipe 已實作但 README 仍寫 planned；沒有降噪模組；`auto-editor` 有 4,984 stars；walkthrough 外接碟今日未掛上。

---

## 選定方案

**證據優先。** 維持 `0.1.x`。先整理工作區與文件，再跑一集真實音檔，再只加深該紀錄指出的那一條。

放棄現在標 1.0。放棄做本機 Descript（文字剪輯桌面軟體）。

---

## 三個階段

### 階段 0 — 衛生（不改產品行為，除了文件）

**狀態：** 已完成，在 `docs/2026-08-17-status-sync`（尚未 push）。

- 2026-05-18 音量／報告修改已收下（`08a165b`），與文件同一分支。
- README 對照表加上 `auto-editor`，recipe 改為已實作，並寫明尚未做降噪。
- SDD 測試數改為現況。
- 19 個 `.claude/worktrees/` 先不動，等明確指示再刪。
- 不要做版本號跳號，不要 `dev` → `main`。

### 階段 1 — 最小真實集數（決策實驗）

需要：使用者擁有的音檔（不進 git）、一個已安裝的 ASR（Belle 或 Qwen3）。

流程：`transcribe`（非 stub）→ `run` → `review serve` → 只自動接受確定性靜音 → 匯出。把時長、剪輯類型數量、審核決定、LUFS／true-peak 目標與實測寫進 `docs/fix-logs/2026-08-XX-real-episode.md`。

同一檔可選跑一次 `auto-editor` 做聽感對照。缺 ffmpeg 或缺該 ASR 就停，不要在同一次再裝第二個模型。

### 階段 2 — 只選一條（看階段 1 紀錄）

| 紀錄寫的是 | 才做 | 不做 |
|---|---|---|
| 剪錯或難以判斷 | 審核頁：點逐字稿 cue 就切換重疊的 operation；上一筆導覽 | 新桌面軟體 |
| 逐字稿不能用 | 只修一個 ASR／對齊問題 | 再加第四家 ASR |
| 匯出過不了音量閘門 | 做完 2026-05-18 的兩次 loudnorm | 接 Auphonic |
| 噪音讓它不能發布 | 可選 DeepFilterNet，且只能 proposed | 預設降噪；未取得同意前不要把來賓音檔上傳 Adobe |
| 最後仍在 Reaper／Premiere 收尾 | 從已接受的 `timeline.v1` 產出 Reaper region EDL | 做成 DAW |

2026-08-17 已核對、但**不插隊**的事實：Auphonic Editor 已能逐段審查並匯出 EDL／Reaper（[2026-04-15 公告](https://auphonic.com/blog/2026/04/15/automatic-video-cutting/)）；Resound 免費 20 分鐘／Creator $15／Studio $60（[定價頁](https://www.resound.fm/pricing)）；Descript 官方 25 語轉寫表沒有中文（[定價頁](https://www.descript.com/pricing)）。這些強化階段 1 要用繁中、以及「若收尾在 DAW 才做 EDL」，不另開平行工作。

### 階段 3 — 發布流程

階段 1 有可發布成品、或有可重現的失敗紀錄之後，再把衛生與證據 commit 推進 `main`。`1.0.0` 還要：README 與程式一致、已出貨命令不再標 planned、`smoke.sh` 通過。

---

## 明確延後

Lattifai decode、桌面包裝、語音克隆、發布上架、雲端協作、MiniMax 當預設、Auphonic 當後端、文字剪輯桌面軟體、繼續擴 provider。

---

## 驗收

- `dev` 乾淨，或 `handover.md` 寫明未提交檔的去向。
- README 對照表有 `auto-editor`，recipe 標已實作。
- SDD 不再把「29 passed」當現況。
- 真實集數 fix-log 有數字，且來源是該次 run 目錄。
- 證據 PR 不夾帶新的 ASR／對齊／說話人分離 provider。
