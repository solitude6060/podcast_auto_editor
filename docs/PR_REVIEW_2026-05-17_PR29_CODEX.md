# PR #29 — Codex code review

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/29
- Base: `dev` → Head: `pr-g/recipe-export-import`
- Head SHA: `5c5372e`
- Review date: 2026-05-17
- Reviewer: Codex (gpt-5.x via codex CLI) invoked as `codex:codex-rescue` subagent
- Verdict: **REQUEST CHANGES**

## Findings

### HIGH
- **`podcast_auto_editor/recipe.py:142`** — `sha256: null` in recipe silently bypasses hash verification. `if expected_sha and ...` is falsy when `expected_sha is None`. A recipe whose `source_media.sha256` was stripped or explicitly set to `null` is silently accepted with any media, no error and no audit trail. Verified by running the exact expression. Breaks the contract in README and the hash-discipline invariant. **Disposition: Fixed in fix round** — explicit `if not expected_sha: raise RecipeError(...)` upfront.

### MEDIUM
- **`tests/test_recipe.py`** — No test for `sha256: null` / missing sha in recipe. 8 tests cover happy path, mismatch, drift override, missing media, and bad schema_version, but the stripped-sha path is uncovered. **Disposition: Folded into Fix #1** — `test_recipe_apply_raises_when_sha256_is_null_in_recipe` added.

### LOW
- **`recipe.py:142`** — `media_drift_allowed` is correctly `False` when `expected_sha is None`, but the rationale is non-obvious because `expected_sha` appears twice in the boolean expression. After the HIGH fix the null path raises before reaching the manifest, so the boolean simplifies to `bool(allow_media_drift and expected_sha != actual_sha)`. **Disposition: Folded into Fix #1.**

## Focus-point summary
- **Hash verification:** HIGH (see above).
- **`apply` must not auto-render:** confirmed clean (`grep -n "render(" recipe.py` returns no results).
- **Schema version gating:** confirmed clean (Python `None != "recipe.v1"` evaluates True, so missing/null schema raises).
- **CLI integration tests:** confirmed end-to-end through `cli.main([...])` — not direct function calls.
- **`media_drift_allowed`:** correct for all reachable non-null cases.
- **Path traversal:** confirmed clean — all three write paths use `out_root / "<static filename>"`; no recipe-controlled strings are used as filesystem paths.
- **Surgical scope:** confirmed — one import line + one 22-line handler block in `cli.py`; zero changes to existing code.

## Confirmed clean

- `render(` does not appear anywhere in `recipe.py` or the CLI handler.
- `schema_version=None` correctly raises (Python `None != "recipe.v1"` is `True`).
- All three output paths anchor to `out_root` with hardcoded filenames; no recipe-controlled paths.
- `_git_sha` catches `OSError`/`SubprocessError`/returns `None` on failure; `_package_version` catches `PackageNotFoundError`/`ImportError`/returns `"unknown"`.
- `_dump_json` uses `sort_keys=True, indent=2` unconditionally — git-friendly idempotency holds for all fields except `generated_at` (timestamps differ by design).
- README flag names match the argparse definitions exactly.
- No new runtime dependencies introduced; all imports are stdlib.
- No `Co-authored-by` trailers in commits.
