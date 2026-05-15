# Fix Log: AI environment doctor

Date: 2026-05-15
Branch: `feature/ai-env-doctor`

## Prompt-to-artifact checklist

- User request: continue development after Docker Compose AI stack; user permits model downloads/integration but warns that other projects may be using GPU.
- Plan artifacts: `docs/plans/2026-05-15-ai-env-doctor.md`, `docs/plans/2026-05-15-ai-env-doctor.zh-TW.md`.
- TDD tests: `tests/test_ai_doctor.py`.
- Implementation: `podcast_auto_editor/ai_doctor.py`, `podcast_auto_editor/cli.py`.
- User-facing docs: `README.md`, `README.zh-TW.md`, `docs/docker-compose-ai-stack.md`, `docs/docker-compose-ai-stack.zh-TW.md`.

## TDD evidence

1. Added failing tests for `ai doctor` module and CLI.
   - Command: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_ai_doctor.py -p no:cacheprovider`
   - Result: collection failed because `podcast_auto_editor.ai_doctor` did not exist.
2. Implemented read-only AI doctor checks for Compose, optional Ollama connectivity, whisper.cpp paths, and MiniMax fallback redaction.
3. Targeted verification:
   - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_ai_doctor.py tests/test_ai_resources.py -p no:cacheprovider`
   - Result: `13 passed in 0.05s`.

## GPU/resource safety

- No model download is automatic in tests, CI, or `ai doctor`.
- Ollama probe is timeout-bounded and can be skipped with `--no-ollama`.
- Missing whisper.cpp paths can be treated as warnings with `--optional-whisper` for lightweight checks.
- Docs recommend pulling small smoke models first and scheduling 30B-class model pulls/runs only when GPU memory is available.

## Deferred / not changed

- No real model download was performed in this branch.
- No heavy GPU inference test was run because user noted another project may be using GPU.

## Final verification evidence

- Full tests: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `160 passed in 2.52s`.
- Syntax/import check: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- Compose syntax: `docker compose --profile ai config` → passed.
- Doctor smoke: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m podcast_auto_editor ai doctor --no-ollama --optional-whisper --format json` → exit 0 with expected warning-only lightweight status.
- Diff whitespace: `git diff --check` → passed.
- Local-only hygiene: `git ls-files .omx` → no tracked `.omx` files.
- Co-author hygiene: recent commit scan for `Co-authored-by` → no matches.
