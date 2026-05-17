# PR #24 — MiniMax code review (via claude-mm)

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/24
- Base: `dev` → Head: `ralph/ai-ui-docker-e2e-closeout`
- Head SHA: `aa1b970a5aa137d5e8c7f3af084a209514e11eb6`
- Review date: 2026-05-17
- Reviewer: `MiniMax-M2.7` via Claude Code CLI configured against `api.minimax.io/anthropic`, invoked with `CLAUDE_CONFIG_DIR=$HOME/.claude-minimax claude -p` against the PR head worktree
- Verdict: **REQUEST CHANGES**

## Findings

### HIGH
- **`scripts/e2e-docker-ai-stack.sh:72-77`** — Fallback path exits 0 but then unconditionally calls `wait_for_running_service ollama`, killing the intended graceful skip. `run_or_exit` on line 74 exits 0 on failure; if the fallback `up -d --no-deps app` succeeds, execution falls through to line 77 `wait_for_running_service ollama` which returns 1 because ollama is not running. Under `set -euo pipefail`, the script exits 1 — false failure. Disposition: **Fixed in fix round** (branch-conditional readiness check + regression test using a `docker` stub).

- **`podcast_auto_editor/local_review_server.py`** — AI draft link 404 in dashboard. `do_GET` only handles `/`, `/index.html`, `/api/status`; HTML `<a href="ai/ai-draft.v1.json">`, `timeline.proposed.v1.json`, `review-session.json` all 404. No test GETs the rendered URL to assert 200. Disposition: **Fixed in fix round** (allowlisted artifact handler + HTTP GET regression tests).

### MEDIUM
- **`local_review_server.py` `_escape` not applied to `ai_draft` path inserted via `link.href`** — `_relative_path` constructs the value from `Path` operations so injection risk is low, but no test exists for path-with-special-chars. Disposition: **Folded into Fix #2** — the new allowlisted artifact handler rejects any path not on the explicit allowlist, closing this gap server-side regardless of client-side escaping.

- **`test_e2e_docker_ai_stack_script.py` lacks fallback-skip assertions** — Only `--dry-run` is tested. Disposition: **Folded into Fix #1** — the new test runs the script with a stubbed `docker` to exercise the fallback path under real `set -e`.

### LOW
- **`ai_drafts.py:291-293`** — `_default_base_url()` / `_default_model()` are called before the dry guard, but neither does network I/O. Concern refuted.
- **`ai_drafts.py:296-299`** — Only `retake_cut` / `speech_cut` operations are AI candidates. Matches PR purpose.
- **`cli.py:679`** — `--dry-run` correctly aliases to `dry_prompt=True` AND `no_net=True`.

## Focus-point summary
- **No-net safety:** PASS (strong assertion in tests).
- **Bash script fallback:** FAIL (HIGH).
- **Dashboard artifact links:** FAIL (HIGH).
- **AI stays review-only:** PASS.
- **Input validation:** PARTIAL — missing-key handling for required timeline fields not tested for silent-wrong-output. Disposition: addressed by Fix #3 (`validate_timeline` wiring).
- **HTML/JSON injection:** MEDIUM (path-with-special-chars not tested); closed by Fix #2 server-side allowlist.
- **Subprocess / HTTP injection:** PASS.
- **Test adequacy (no-network):** PASS unit; WEAK script (closed by Fix #1 test).
- **Surgical-changes:** PASS.
