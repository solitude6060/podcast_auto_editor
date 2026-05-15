# Fix Log: AI model catalog and manual pull plan

Date: 2026-05-15
Branch: `feature/ai-model-plan`

## Prompt-to-artifact checklist

- User request: continue development; model downloads are allowed for integration/testing but GPU is shared, so tests must be resource careful.
- Plan artifacts: `docs/plans/2026-05-15-ai-model-plan.md`, `docs/plans/2026-05-15-ai-model-plan.zh-TW.md`.
- TDD tests: `tests/test_ai_models.py`.
- Implementation: `podcast_auto_editor/ai_models.py`, `podcast_auto_editor/cli.py`.
- User-facing docs: `README.md`, `README.zh-TW.md`, `docs/docker-compose-ai-stack.md`, `docs/docker-compose-ai-stack.zh-TW.md`.

## TDD evidence

1. Added failing tests for a model catalog and manual pull planner.
   - Command: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_ai_models.py -p no:cacheprovider`
   - Result: collection failed because `podcast_auto_editor.ai_models` did not exist.
2. Implemented model catalog and `ai models` CLI.
3. Targeted verification:
   - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_ai_models.py -p no:cacheprovider`
   - Result: `6 passed in 0.05s`.

## GPU/resource safety

- `ai models --pull-plan` prints commands only and never executes `ollama pull`.
- Smoke tier is the safe default when the GPU is shared.
- Heavy 30B-class model is marked `heavy-manual` and not GPU-shared safe.
- No downloads or inference run in tests or CI.

## Deferred / not changed

- No actual model was downloaded in this branch.
- No live GPU inference smoke was run.

## Final verification evidence

- Full tests: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `166 passed in 3.37s`.
- Syntax/import check: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- Compose syntax: `docker compose --profile ai config` → passed.
- Pull-plan smoke: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m podcast_auto_editor ai models --tier smoke --pull-plan` → printed manual command only.
- Diff whitespace: `git diff --check` → passed.
- Local-only hygiene: `git ls-files .omx` → no tracked `.omx` files.
- Co-author hygiene: recent commit scan for `Co-authored-by` → no matches.

## Qwen 3.6 local API update

- User clarified the existing model is API-format, not a model that should be downloaded by this project.
- Endpoint: `http://127.0.0.1:9090/v1`.
- Model name: `qwen3.6-27b-turbo3`.
- Capability notes: 128k context and VL / vision-understanding capability.
- API verification:
  - `/v1/models` returned HTTP 200 and listed `qwen3.6-27b-turbo3`.
  - Minimal `/v1/chat/completions` smoke returned HTTP 200 with `total_tokens=23`; no heavy load test was run.
  - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m podcast_auto_editor ai models --readiness --tier api-local --no-ollama --timeout 3 --format json` → `overall_status: ok`, `installed: 1/1`.
