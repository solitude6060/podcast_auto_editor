# PR #24 — Gemini code review

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/24
- Base: `dev` → Head: `ralph/ai-ui-docker-e2e-closeout`
- Head SHA: `aa1b970a5aa137d5e8c7f3af084a209514e11eb6`
- Review date: 2026-05-17
- Reviewer: `gemini-3.1-pro-preview` invoked via `gemini --skip-trust -p ... -m gemini-3.1-pro-preview`
- Verdict: **REQUEST CHANGES**

## Findings

### HIGH
- **`scripts/e2e-docker-ai-stack.sh:78-79`** — The script's fallback behavior is fundamentally broken by `set -e`. If the full stack startup (`up -d ollama app`) fails, the script drops down to `up -d --no-deps app`. However, it unconditionally waits for `ollama` to become ready immediately after. Since `ollama` is not running in the fallback path, `wait_for_running_service ollama` times out and returns `1`. Due to `set -euo pipefail`, the script exits instantly and bypasses the `app` smoke test entirely. Disposition: **Fixed in fix round** (test + branch-conditional readiness check).

- **`podcast_auto_editor/local_review_server.py:98-102` (and unpatched `do_GET` handler)** — The new HTML dashboard introduces active `<a href="...">` links for `timeline.proposed.v1.json`, `review-session.json`, and the generated AI draft path. However, the existing `ReviewRequestHandler.do_GET` only serves `/`, `/index.html`, and `/api/status`, intentionally returning an HTTP 404 error for all other requests. Clicking any of the newly added artifact links results in a 404. Disposition: **Fixed in fix round** (allowlisted static artifact handler with path-traversal guard + HTTP GET regression tests).

### LOW
- **`podcast_auto_editor/ai_drafts.py:57-58`** — `float(segment.get("start", 0.0))` raises `TypeError` if a malformed JSON payload explicitly includes `"start": null`. Disposition: **Deferred** to follow-up; no production complaint, low-impact edge case.

## Focus-point summary
- **No-net safety:** Verified. No eager network at module load; guards correctly placed.
- **Bash script correctness:** Confirmed broken (see HIGH above).
- **AI draft link reachability:** Confirmed broken (see HIGH above).
- **AI stays review-only:** Verified.
- **Input validation:** Verified for transcript/timeline shape coercions.
- **HTML/JSON injection:** Verified — DOM primitives (`textContent`, `link.href`) safely encode.
- **Subprocess / HTTP injection:** Verified.
- **Test adequacy:** Verified for offline payload construction and no-network monkeypatching.
- **Surgical-changes principle:** Verified.
