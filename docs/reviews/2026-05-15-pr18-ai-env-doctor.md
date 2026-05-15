# PR 18 Review: AI environment doctor

Date: 2026-05-15
PR: https://github.com/solitude6060/podcast_auto_editor/pull/18
Branch: `feature/ai-env-doctor` → `dev`

## Review scope

- Read-only `ai doctor` checks for Compose, Ollama, whisper.cpp, and MiniMax fallback wiring.
- GPU/resource safety when another project may be using the GPU.
- Secret redaction and local-first behavior.
- English and Traditional Chinese user docs.

## Findings

| Finding | Severity | Resolution |
| --- | --- | --- |
| Doctor must not trigger large downloads or GPU inference by default. | High | Implementation only reads files/env and uses a timeout-bounded optional Ollama tags request. |
| MiniMax API key must never be printed. | High | Report returns only `<redacted>` and configured boolean. |
| Shared GPU usage needs a safe path. | Medium | Added `--no-ollama` and `--optional-whisper`; docs recommend small smoke models and scheduled large model pulls. |
| User-facing docs need Traditional Chinese coverage. | Medium | Updated README.zh-TW and Docker Compose zh-TW docs. |

## Verification evidence

Local:

- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_ai_doctor.py tests/test_ai_resources.py -p no:cacheprovider` → `13 passed in 0.05s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `160 passed in 2.52s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- `docker compose --profile ai config` → passed.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m podcast_auto_editor ai doctor --no-ollama --optional-whisper --format json` → exit 0 with warning-only lightweight status.
- `git diff --check` → passed.
- `git ls-files .omx` → no tracked `.omx` files.
- Recent commit trailer grep for `Co-authored-by` → no matches.

CI:

- GitHub Actions CI run `25905155484` → success.

## Decision

Approved for merge into `dev`.
