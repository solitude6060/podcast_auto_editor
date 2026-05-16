# PR #24 — Codex code review

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/24
- Base: `dev` → Head: `ralph/ai-ui-docker-e2e-closeout`
- Head SHA: `aa1b970a5aa137d5e8c7f3af084a209514e11eb6`
- Review date: 2026-05-17
- Reviewer: Codex (gpt-5.x via codex CLI) invoked as `codex:codex-rescue` subagent
- Verdict: **REQUEST CHANGES**

## Findings

### HIGH
- **`scripts/e2e-docker-ai-stack.sh:72-78`** — Docker app-only fallback still waits for missing `ollama`. After falling back from `up -d ollama app` to `up -d --no-deps app`, the script unconditionally runs `wait_for_running_service ollama`, which under `set -euo pipefail` exits the script after timeout. This defeats the intended graceful fallback at lines 72–74. Disposition: **Fixed in fix round** (track `full_stack_ok` state; only wait for ollama when full stack started; add test asserting exit 0 in degraded path).

- **`podcast_auto_editor/local_review_server.py:110-112, 144-154, 255-268`** — Dashboard artifact links are rendered but unreachable. HTML emits links to `timeline.proposed.v1.json`, `review-session.json`, AI draft; `do_GET` only handles `/`, `/index.html`, `/api/status`. Existing tests only assert HTML labels + `load_review_context()` return values — no GET assertion. Disposition: **Fixed in fix round** (allowlisted static file serving restricted to known artifact filenames under `run_dir` with path-traversal protection + HTTP GET 200/404 tests).

### MEDIUM
- **`podcast_auto_editor/cli.py:681-695`, `podcast_auto_editor/ai_drafts.py:295-300`** — `ai draft` skips timeline validation. If `operations` is missing, non-list, or malformed, the call either silently produces a zero-candidate draft or raises an uncaught exception. The project already has `validate_timeline()` (`timeline.py:61-124`) used by `validate` and `validate-run`. Disposition: **Fixed in fix round** — call `validate_timeline()` on the loaded timeline before `generate_ai_draft()`, and return a clean CLI error on failure. Add regression tests for missing/non-list/invalid `operations`.

## Focus-point summary
- **No-network guarantee (`--dry-prompt` / `--dry-run`):** Low risk. HTTP isolated to `chat_with_local_ai()`, only invoked after dry/no-net early-return paths exit. `ai draft --dry-run` maps to both `dry_prompt=True` and `no_net=True` at `cli.py:691-692`. No subprocess in dry paths.
- **Bash script fallback:** HIGH (see above).
- **Dashboard artifact link reachability:** HIGH (see above).
- **Test isolation:** Low risk; `tmp_path`/`monkeypatch` used throughout new tests.
- **Security:** No hardcoded credentials; `api_key` is optional in-memory header only; localhost-only review server. If artifact serving is added, paths must be constrained to `run_dir` (addressed by Fix #2's allowlist).

## Confirmed clean
- New AI HTTP client is not constructed at module import time; `urllib.request.urlopen` only called inside `chat_with_local_ai()`.
- `ai draft` writes to separate `ai/ai-draft.v1.json` artifact and does not mutate timeline operation state.
- Existing render gates in `cli.py` intact: proposed timelines refused without `--accept-safe-defaults`; accepted retake/speech-changing operations still require safe-policy clearance or explicit manual review.
- No hardcoded secrets, no `.omx` tracking references, no `Co-authored-by` trailers.
