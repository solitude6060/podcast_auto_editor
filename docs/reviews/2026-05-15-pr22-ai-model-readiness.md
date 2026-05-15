# PR 22 Review: local API model readiness

Date: 2026-05-15
PR: https://github.com/solitude6060/podcast_auto_editor/pull/22
Branch: `feature/ai-model-readiness` → `dev`

## Review scope

- Use existing llama.cpp/OpenAI-compatible Qwen3.6 27B Turbo3 API instead of downloading a duplicate model.
- Add `ai models --readiness` for OpenAI-compatible `/v1/models` and Ollama `/api/tags` checks.
- Preserve shared-GPU safety by avoiding long-context, VL, or heavy inference tests.

## Findings

| Finding | Severity | Resolution |
| --- | --- | --- |
| User clarified model is API-format and should not be downloaded. | High | `api-local` now defaults to `http://127.0.0.1:9090/v1` and `qwen3.6-27b-turbo3`; pull plan emits no command for this tier. |
| Readiness should prove availability without heavy GPU use. | High | `/v1/models` readiness check detects installed model; minimal chat smoke was 23 tokens only. |
| VL/128k capability should be recorded but not stress-tested. | Medium | Catalog records `context_window=128000` and `vision_understanding`; heavy VL/long-context tests deferred. |

## Verification evidence

Local:

- `/v1/models` at `http://127.0.0.1:9090/v1` returned HTTP 200 and listed `qwen3.6-27b-turbo3`.
- Minimal `/v1/chat/completions` smoke returned HTTP 200 with `total_tokens=23`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_ai_model_readiness.py tests/test_ai_models.py -p no:cacheprovider` → `13 passed in 1.30s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `173 passed in 3.07s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m podcast_auto_editor ai models --readiness --tier api-local --no-ollama --timeout 3 --format json` → `overall_status: ok`, `installed: 1/1`.
- `docker compose --profile ai config`, `compileall`, `git diff --check`, `.omx` and co-author hygiene checks passed.

CI:

- GitHub Actions CI run `25912868638` → success.

## Decision

Approved for merge into `dev`.
