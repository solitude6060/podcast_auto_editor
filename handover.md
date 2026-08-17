# handover.md

Last updated: 2026-08-17

## 繁體中文快照

這次後續 session 做完不需拍板的工程：修 CUDA 主機上 pyannote 測試崩潰、收下 2026-05-18 音量／報告修改、對齊 README／SDD／`user_todo`。分支 `docs/2026-08-17-status-sync`，尚未 push。下一手：你提供真實音檔與一個已安裝的語音辨識。不要從 1.0 簽核接著做。

---

## This session (engineering follow-up)

- Interpreted “complete every no-decision engineering item” as Phase 0 only.
- Did **not**: bump `0.1.0`, run a real episode, delete 19 worktrees, push, or open a PR.
- Branch: `docs/2026-08-17-status-sync` from `dev` `2c9a81d` (same checkout, no extra worktree).
- `86d9560` — `fix: skip CUDA move when pyannote pipeline has no .to`
- `08a165b` — `feat: two-pass loudnorm and per-profile quality reports`
- `21e68ba` — `docs: sync README, SDD, and status with 2026-08-17 review`
- Verification (before the docs commit; docs do not change tests):

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider
# 314 passed, 11 skipped
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests
git ls-files .omx
# empty
```

## Next session starts here

1. Phase 1 needs a local audio file the user owns and one installed non-stub ASR.
2. Do **not** bump `0.1.0` → `1.0.0`.
3. Push / PR this branch only if the user asks.
4. Leave `.claude/worktrees/` locked until the user asks.

## Operator notes

- Verification command in project AGENTS.md still uses `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor` (scratch cache only).
- Keep `.omx/`, `.omc/`, `.claude/`, `runs/`, media, and credentials untracked.
- MiniMax key must stay ephemeral if used.

## Do not resume

- `user_todo.md` B1–B3 (release date / 1.1 defer list / release branch) as the next autopilot gate.
- Adding Lattifai decode or another ASR provider before a real episode.
- Discarding `08a165b` (the quality patch was complete and kept).
