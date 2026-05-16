# PR #29 — MiniMax code review (via claude-mm)

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/29
- Base: `dev` → Head: `pr-g/recipe-export-import`
- Head SHA: `5c5372e`
- Review date: 2026-05-17
- Reviewer: `MiniMax-M2.7` via Claude Code CLI against `api.minimax.io/anthropic`
- Verdict: **REQUEST CHANGES**

## Findings

### MEDIUM (calibrated to HIGH per Gemini + Codex agreement; see triage in PR comment)
- **`podcast_auto_editor/recipe.py:140-146`** — Silent sha256 bypass when recipe is stripped. `if expected_sha and expected_sha != actual_sha and not allow_media_drift` short-circuits to False when `expected_sha is None`. MiniMax calibrated this MEDIUM citing "the manifest still reflects no drift override". Gemini and Codex both calibrated HIGH because the README and SDD treat sha verification as a hard invariant. Final HIGH per the majority + invariant-first rule. **Disposition: Fixed in fix round.**

- **`tests/test_recipe.py` and `recipe.py:131-134`** — `schema_version: null` is not regression-tested. Current code correctly raises (because `None != "recipe.v1"`), but a regression test is required per project TDD discipline. **Disposition: Folded into Fix #1.**

### LOW
- **`recipe.py:164`** — `media_drift_allowed` reads correctly for non-null sha; for null sha it produces a potentially-misleading `False`. After the HIGH fix the null sha path raises before reaching the manifest, eliminating the ambiguity. **Disposition: Folded into Fix #1's simplified boolean expression.**

## Focus-point summary
- **Hash verification:** MEDIUM (calibrated to HIGH; see above).
- **`apply` must not auto-render:** verified clean.
- **Schema version gating:** verified clean; regression test gap noted.
- **Recipe JSON canonical:** verified.
- **Path traversal:** verified clean.
- **`_git_sha` / `_package_version`:** verified graceful degradation.
- **`apply` writing manifest:** correct for all non-null cases.
- **CLI integration tests:** verified end-to-end.
- **Surgical scope:** verified.
- **Docs accuracy:** verified.
