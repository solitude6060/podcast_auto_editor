# PR #29 — Gemini code review

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/29
- Base: `dev` → Head: `pr-g/recipe-export-import`
- Head SHA: `5c5372e`
- Review date: 2026-05-17
- Reviewer: `gemini-3.1-pro-preview` via `gemini --skip-trust -p ... -m gemini-3.1-pro-preview`
- Verdict: **REQUEST CHANGES**

## Findings

### HIGH
- **`podcast_auto_editor/recipe.py:143`** — Silent verification bypass. When `expected_sha` is `None` (e.g., `sha256: null` or stripped from the recipe), the condition `if expected_sha and expected_sha != actual_sha` short-circuits to `False` and apply proceeds without verifying media integrity. Violates the README contract ("apply verifies the source media sha256") and the hash-discipline invariant. **Disposition: Fixed in fix round** — explicit `if not expected_sha: raise RecipeError(...)` before the mismatch check.

### MEDIUM
- **`podcast_auto_editor/recipe.py:165`** — `media_drift_allowed` audit field is `False` when `expected_sha` is missing/null even if user passed `--allow-media-drift`, because the boolean expression requires `expected_sha` to be truthy. After the HIGH fix the null path raises before reaching the manifest, making this case unreachable; the boolean is simplified to `bool(allow_media_drift and expected_sha != actual_sha)`. **Disposition: Folded into Fix #1.**

## Focus-point summary
- **Hash verification correctness:** FAILED (see HIGH).
- **`apply` must not auto-render:** verified clean.
- **Schema version gating:** verified clean (null `schema_version` correctly raises).
- **Recipe JSON canonical:** verified (`sort_keys=True, indent=2`).
- **Path traversal:** verified clean (all writes are `out_root / "<static filename>"`).
- **`_git_sha` / `_package_version` failure modes:** verified clean.
- **`apply` writing manifest:** FAILED for the null-sha edge (folded into Fix #1).
- **CLI integration tests:** verified end-to-end through `cli.main([...])`.
- **Surgical scope:** verified — no opportunistic refactors.
- **Docs accuracy:** verified — README flags match parser exactly.
