# tracker.md

Last updated: 2026-08-17

## 繁體中文快照

階段 0 已完成（尚未 push）。進行中：無實作任務。下一步是階段 1（一集真實音檔）。1.0 簽核、Lattifai decode、桌面軟體、降噪、再加 ASR 品牌均延後。

---

## Tracks

| Track | Status | Next item |
|---|---|---|
| Hygiene / docs sync | done on branch | Push / PR only if the operator asks |
| Loudness / export | landed `f70f7ac` | Re-measure on a real episode |
| Pyannote CUDA host crash | landed `d02b1b8` | None |
| Real-episode evidence | pending | Operator audio + one ASR; fix-log |
| Review UX | deferred | Only if Phase 1 says cuts are hard to judge |
| Chinese ASR quality | adapters exist | Real run not done; Belle real test is env-gated |
| Provider expansion | stopped | No new ASR / align / diarize brands |
| 1.0 release | superseded | Replaced by evidence-first plan |
| `dev` → `main` | stalled | 40 commits; wait for Phase 1 evidence |

## Near-term queue

1. Operator: mount or provide a real episode (do not commit the media).
2. Operator: install one non-stub ASR if Phase 1 should run.
3. Operator session: Phase 1 real episode + fix-log.
4. Then exactly one Phase 2 wedge.

## Deferred

- Lattifai decode body
- Review UI previous-operation key
- macOS / WSL CI
- Packaged desktop app
- DeepFilterNet / denoise (unless Phase 1 names noise)
- NLE / AAF export (unless Phase 1 names DAW finish)
- MiniMax as default LLM
- Publishing / cloud collaboration
- Deleting 19 locked `.claude/worktrees/`
