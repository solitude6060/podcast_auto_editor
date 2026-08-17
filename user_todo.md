# user_todo.md — items that need the operator

Tracks blockers that require a human. Autopilot must not treat the
2026-05-18 MVP 1.0 sign-off (B1 / B2 / B3) as the next gate.

Date opened: 2026-05-18  
Superseded: 2026-08-17 by `docs/plans/2026-08-17-adjustment-and-next.md` (ADR Option A)

## 繁體中文

1.0 版本號、發布日期、`dev` 還是 `release/1.0`，都還不用回。下一步能改變「繼續／調整／停」的，是一集你擁有權利的真實口語音檔，加上一個已安裝的非 stub 語音辨識。不要把媒體 commit 進 git。19 個鎖住的 worktree 先留著。

---

## Current blockers (Phase 1)

| # | Item | What you do | Why | Blocking? |
|---|---|---|---|---|
| P1 | Real spoken episode | Provide a rights-owned WAV/MP3 (prefer 繁中, about 10–30 min). Do not commit the media. | Next continue / adjust / stop bit | **Yes** for Phase 1 |
| P2 | One installed ASR | Install one of `faster-whisper`, `whisper.cpp`, or `qwen-asr` if you want non-stub evidence | A stub-only run is not Phase 1 evidence | **Yes** for Phase 1 |

Walkthrough: `docs/walkthroughs/real-podcast-ep1.md`.  
Do not bump `0.1.0` → `1.0.0` until a real-episode fix-log exists.

## Optional (not blocking hygiene)

| # | Item | What you do | Why | Blocking? |
|---|---|---|---|---|
| A1 | Belle weights | Download `BELLE-2/Belle-whisper-large-v3-zh` if you choose that ASR | Env-gated integration test | No |
| A2 | Short Chinese fixture | 5–10 s `.wav` at `tests/fixtures/zh_sample.wav` or `PAE_BELLE_REAL_AUDIO` | Belle real-load test | No |
| W1 | Locked worktrees | Say whether to delete the 19 trees under `.claude/worktrees/` | Disk / clutter only | No |

## Superseded — do not resume as the next gate

| # | Item | Status |
|---|---|---|
| B1 | Version bump `0.1.0` → `1.0.0` | Superseded. Stay on `0.1.x`. |
| B2 | Confirm deferred-to-1.1 list | Superseded. Evidence-first plan owns scope. |
| B3 | `dev` vs `release/1.0` | Superseded. Do not promote `dev` → `main` until Phase 1 evidence exists. |

## Things you do not need to action for Phase 0

- Triple-review keys
- HF_TOKEN unless you run real pyannote
- Discarding or keeping the 2026-05-18 quality patch (landed on `docs/2026-08-17-status-sync`)
- Push / PR (not opened unless you ask)

---

## Status log

- 2026-05-18 opened by autopilot. Planning PR-X2.1 in worktree (codex planner running). Audit punch list assembled.
- 2026-05-18 PR-X2.1 plan + RED test + walkthrough committed on feature/pr-x2-1-belle-real-integration; awaiting operator-provided Belle model + Chinese audio fixture per items A1/A2 above.
- 2026-05-18 triple-review (Gemini 2.5-pro + MiniMax + codex-family). Codex caught the wrapper-drops-model HIGH that MiniMax+Gemini missed. 5 findings fixed; 2 LOW skipped per reviewer calibration. See docs/PR_REVIEW_2026-05-18_PR47_*.md.
- **2026-05-18 PR #47 merged to `dev`** as `4129319` (`gh pr merge --merge`, TDD pair history preserved). 305 tests passed, 11 skipped.
- 2026-05-18 PR #48 opened (Mini workflow): one-line CLI help text fix for stale "lattifai deferred to PR-X4.1" ref. Auto-merge enabled; merges when CI completes.
- 2026-05-18 **MVP 1.0 punch list reduced to user sign-off (B1/B2/B3)**. That gate is no longer current.
- **2026-08-17** Phase 0 hygiene on `docs/2026-08-17-status-sync`. B1–B3 superseded by ADR Option A. Next operator input is P1 + P2.
