# status.md

Last updated: 2026-08-17

## 繁體中文快照

階段 0 已落在 `docs/2026-08-17-status-sync`：`d02b1b8`（pyannote CUDA `.to`）、`f70f7ac`（two-pass loudnorm／報告）、以及同分支的文件對齊。驗證：314 passed、11 skipped、`compileall` 通過。版本仍是 `0.1.0`。沒有 push、沒有開 PR、沒有 `dev` → `main`。下一步要你提供一集真實口語音檔與一個已安裝的非 stub 語音辨識。

---

## Evidence / progress

- **Feature branch:** `docs/2026-08-17-status-sync` off `dev` `2c9a81d`.
- **Phase 0 commits:** `d02b1b8` (CUDA `.to` guard), `f70f7ac` (loudnorm / reports). Docs commit is the tip of this branch after the hygiene PR lands.
- **Production branch:** `main` @ `ae3ec41`. `dev` remains 40 commits ahead of `main`; this branch is not promoted.
- **Tests:** 314 passed, 11 skipped (325 collected) on 2026-08-17 after the new pyannote regression.
- **Version:** `0.1.0` in `pyproject.toml`. Do not bump to `1.0.0`.
- **Last real-episode attempt:** synthetic 4 s silence plus stub walkthrough. Walkthrough disk `/media/ma/1AF83466F83441F5` was unmounted on 2026-08-17.

## Latest decisions (2026-08-17)

- ADR Option A: evidence-first. Stay on `0.1.x`.
- Keep the 2026-05-18 quality patch (complete TDD pair).
- Product sentence: local + per-edit review + `recipe.v1` + measured publish gates + optional Chinese ASR.
- Do not compete with WyattBlue `auto-editor` on CLI silence-cut.
- Do not start a local Descript clone.

## Risk radar

| Item | Level | Note |
|---|---|---|
| No publishable real episode | high | Blocks continue / adjust / stop |
| README / SDD drift | resolved on this branch | Recipe marked implemented; SDD cites 325 collected |
| 19 locked worktrees in `.claude/worktrees/` | medium | Untouched; do not delete without asking |
| `main` 40 commits behind | medium | Wait for Phase 1 evidence |

## Canonical docs

- SDD: `docs/sdd/podcast-auto-editor-mvp.md`
- Review: `docs/reviews/2026-08-17-project-status-review.md`
- Landscape: `docs/research/2026-08-17-competitor-landscape.md`
- Plan: `docs/plans/2026-08-17-adjustment-and-next.md`
