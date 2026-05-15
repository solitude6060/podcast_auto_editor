# Dev-to-Main Stage Review: local API model readiness

Date: 2026-05-15
PR: https://github.com/solitude6060/podcast_auto_editor/pull/23
Branch: `dev` → `main`

## Scope

Promote the Qwen3.6 local API readiness support after PR #22 merged into `dev` and fixture isolation was fixed on `dev`.

## Evidence checklist

- Feature PR review exists: `docs/reviews/2026-05-15-pr22-ai-model-readiness.md`.
- `api-local` defaults to `http://127.0.0.1:9090/v1` and `qwen3.6-27b-turbo3`.
- Catalog records 128k context and `vision_understanding` capability.
- No duplicate model download path is required for the existing API model.
- `.omx` remains untracked and no `Co-authored-by` trailers were introduced.

## Verification on `dev`

- `/v1/models` at `http://127.0.0.1:9090/v1` returned HTTP 200 and listed `qwen3.6-27b-turbo3`.
- Minimal `/v1/chat/completions` smoke returned HTTP 200 with `total_tokens=23`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `173 passed in 3.01s` after fixture isolation fix.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m podcast_auto_editor ai models --readiness --tier api-local --no-ollama --timeout 3 --format json` → `overall_status: ok`, `installed: 1/1`.
- `compileall`, `docker compose --profile ai config`, `git diff --check`, `.omx` and co-author hygiene checks passed.

## CI

- Feature PR #22 latest CI run `25912919563` → success.
- Dev-to-main PR #23 CI run `25912987223` → success.

## Decision

Approved for merge from `dev` into `main`.
