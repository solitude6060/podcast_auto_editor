# PR #30 — Codex code review

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/30
- Base: `dev` → Head: `pr-b/dashboard-diff-review`
- Head SHA: `6e8ff45`
- Review date: 2026-05-17
- Reviewer: Codex (gpt-5.x via codex CLI) invoked as `codex:codex-rescue` subagent
- Verdict: **REQUEST CHANGES**

## Findings

### MEDIUM
- **F-1 — `local_review_server.py:254`** — `j` and `k` both call `refresh()`, so `k` cannot navigate to a previous item. Does not match the Stage 1 plan's `j/k` next/prev contract. **Disposition: Documented as forward-only** — CHANGELOG updated to clarify the current behaviour; real prev navigation deferred to a follow-up PR. Inline JS comment added.

- **F-2 — `local_review_server.py:345`** — Operation-id guard does not percent-decode the slice. Literal `../foo`, `../../etc/passwd`, `/etc/passwd` are rejected (contain `/` or match `..`); `%2e%2e`, `%2Fetc%2Fpasswd`, `%00` are NOT rejected by the guard itself and only 404 because `find_operation` returns None for those exact encoded ids. Hardening recommended. **Disposition: Fixed in fix round** — `urllib.parse.unquote` is applied before the guard; control characters and the decoded `/` / `\` / `.` / `..` are rejected.

### LOW
- **F-3 — `tests/test_local_review_server.py:155`** — `_spawn_with_multi_op` shuts down the server via `server.shutdown()` only; `server_close()` is not called and the thread is not joined. `shutdown()` stops `serve_forever` but does not close the listening socket. **Disposition: Fixed in fix round** — helper updated to call `server_close()` and join the thread with a timeout.

## Focus-point summary
- **Path-traversal guard:** literal forms caught; encoded forms missed (see F-2). Final HIGH-after-fix coverage.
- **`parse_qs` empty filter:** confirmed correct.
- **Keyboard handler input check:** confirmed correct.
- **Timeline mutation:** confirmed safe.
- **Payload shape mismatch:** flagged as maintainability risk; Gemini + MiniMax escalated to HIGH/CRITICAL respectively; final HIGH per the majority. **Disposition: Fixed via `explain_operation`-backed canonicalisation.**

## Confirmed clean
- Filter narrowing uses equality only; no injection vector.
- Aggregate counts remain unfiltered.
- No new dependency files; only stdlib `parse_qs` added.
- PR scoped to four files; no opportunistic refactors elsewhere.
- No `Co-authored-by` trailers.
- TDD pair ordering (`dfe1210` tests first, `6e8ff45` implementation) correct.
