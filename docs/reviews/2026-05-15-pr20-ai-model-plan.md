# PR 20 Review: AI model catalog and manual pull plan

Date: 2026-05-15
PR: https://github.com/solitude6060/podcast_auto_editor/pull/20
Branch: `feature/ai-model-plan` → `dev`

## Review scope

- Local model catalog tiers for smoke, recommended, and heavy-manual models.
- Manual Ollama pull-plan output that does not execute downloads.
- Shared-GPU safety while another project may be using GPU.
- English and Traditional Chinese docs.

## Findings

| Finding | Severity | Resolution |
| --- | --- | --- |
| CLI must not download models unexpectedly. | High | `ai models --pull-plan` prints commands only; tests monkeypatch `subprocess.run` and verify it is not called. |
| Shared GPU requires a low-resource path. | High | Smoke tier uses a small model and is the documented shared-GPU default. |
| Heavy models need manual scheduling. | Medium | `qwen3:32b` is marked `heavy-manual` and `gpu_shared_safe=false`. |
| User-facing docs require Traditional Chinese coverage. | Medium | README.zh-TW and Docker Compose zh-TW docs were updated. |

## Verification evidence

Local:

- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_ai_models.py -p no:cacheprovider` → `6 passed in 0.05s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `166 passed in 3.37s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- `docker compose --profile ai config` → passed.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m podcast_auto_editor ai models --tier smoke --pull-plan` → printed manual command only.
- `git diff --check` → passed.
- `git ls-files .omx` → no tracked `.omx` files.
- Recent commit trailer grep for `Co-authored-by` → no matches.

CI:

- GitHub Actions CI run `25911521036` → success.

## Decision

Approved for merge into `dev`.
