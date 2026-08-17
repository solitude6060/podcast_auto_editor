# tracker.md

Last updated: 2026-08-17

## 繁體中文快照

階段 0 審查已做，F1／F2／F3 已修。進行中：無實作任務。下一步是階段 1（一集真實音檔）。尚未 push。

---

## Tracks

| Track | Status | Next item |
|---|---|---|
| Hygiene / docs sync | done on branch | Push / PR only if the operator asks |
| Phase 0 code review | REQUEST CHANGES then fixed | F4 deferred |
| Loudness / export | landed + F1/F2 fix | Re-measure on a real episode |
| Pyannote CUDA host crash | landed `86d9560` | None |
| Real-episode evidence | pending | Operator audio + one ASR; fix-log |
| Review UX | deferred | Only if Phase 1 says cuts are hard to judge |
| Chinese ASR quality | adapters exist | Real run not done |
| Provider expansion | stopped | No new ASR / align / diarize brands |
| 1.0 release | superseded | Evidence-first plan |
| `dev` → `main` | stalled | Wait for Phase 1 evidence |

## Near-term queue

1. Operator: mount or provide a real episode (do not commit the media).
2. Operator: install one non-stub ASR if Phase 1 should run.
3. Operator: say whether to push / open a PR into `dev`.
4. Then Phase 1 real episode + fix-log.

## Deferred

- F4: incomplete loudnorm JSON as `KeyError` (same as `measure_audio_quality`)
- Lattifai decode body
- Review UI previous-operation key
- macOS / WSL CI
- Packaged desktop app
- DeepFilterNet / denoise (unless Phase 1 names noise)
- NLE / AAF export (unless Phase 1 names DAW finish)
- MiniMax as default LLM
- Publishing / cloud collaboration
- Deleting 19 locked `.claude/worktrees/`
