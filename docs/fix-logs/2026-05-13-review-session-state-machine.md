# Review session state machine implementation log

## Scope
A6 first full increment: local review session JSON with replayable accept/reject/undo decisions, status summaries, and CLI commands for status, decision append, and timeline rebuild.

## Changes
- Added `podcast_auto_editor/review_session.py`.
- Review sessions use `schema_version: review-session.v1`, `source_timeline`, and append-only `decisions`.
- Decisions support `accept`, `reject`, and `undo` with reviewer, note, and timestamp.
- Replay rebuilds timeline operation states, manual review provenance, and recovery metadata from proposed timeline + latest decisions.
- Added CLI commands:
  - `podcast-auto-editor review status <session> [--format json|markdown]`
  - `podcast-auto-editor review decide <session> --operation-id ... --decision accept|reject|undo --reviewer ...`
  - `podcast-auto-editor review rebuild <session> --timeline <proposed> --out <accepted>`

## Verification
- Red tests first: `podcast_auto_editor.review_session` and review subcommands were missing.
- Targeted green: review session module + CLI tests → `8 passed`.
- Full regression: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `93 passed`.
