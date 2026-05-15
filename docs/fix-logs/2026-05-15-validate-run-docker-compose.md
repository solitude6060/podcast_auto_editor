# Fix Log: validate-run and Docker Compose local AI stack

Date: 2026-05-15
Branch: `feature/validate-run-command`

## Prompt-to-artifact checklist

- Continue development autonomously: implemented a validation preflight and Docker Compose local AI stack.
- Docker Compose AI environment: `compose.yaml`, `Dockerfile`, `.dockerignore`, `.env.example`, `docs/docker-compose-ai-stack.md`, `docs/docker-compose-ai-stack.zh-TW.md`.
- Strict SDD/TDD planning: `docs/plans/2026-05-15-validate-run-command.md`, `docs/plans/2026-05-15-validate-run-command.zh-TW.md`, `docs/plans/2026-05-15-docker-compose-ai-stack.md`, `docs/plans/2026-05-15-docker-compose-ai-stack.zh-TW.md`.
- TDD tests: `tests/test_cli.py`, `tests/test_docker_compose.py`.
- User-facing Traditional Chinese docs: `README.zh-TW.md`, `docs/docker-compose-ai-stack.zh-TW.md`.
- Local-only hygiene: `.env`, models, generated runs, and `.omx` remain ignored/local-only.

## TDD evidence

1. Added failing `validate-run` CLI tests.
   - Command: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_cli.py -p no:cacheprovider`
   - Result: `5 failed, 30 passed`
   - Cause: `validate-run` command did not exist yet.
2. Implemented parser, config/timeline/transcript preflight, and transcript duration checks.
3. Added Docker Compose safety tests for services, GPU reservation, localhost binding, secret placeholders, dockerignore, and Traditional Chinese docs.
4. Targeted verification:
   - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_cli.py tests/test_docker_compose.py -p no:cacheprovider`
   - Result: `38 passed in 0.18s`

## Design notes

- `ollama` is an optional local GPU service and is bound to `127.0.0.1` only.
- Compose uses NVIDIA GPU reservations under `deploy.resources.reservations.devices`.
- The app container uses uv and mounts local source/runs/models instead of baking model files into the image.
- MiniMax remains a blank `.env.example` placeholder and is not enabled by default.

## Deferred / not changed

- No model download automation was added.
- No real Docker daemon / GPU smoke was run in this feature branch yet.
- No cloud ASR/LLM adapter was added.

## Final verification evidence

- Full tests: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `155 passed in 2.68s`.
- Syntax/import check: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- Diff whitespace: `git diff --check` → passed.
- Local-only hygiene: `git ls-files .omx` → no tracked `.omx` files.
- Co-author hygiene: recent commit scan for `Co-authored-by` → no matches.
- Compose syntax: `docker compose --profile ai config` → passed.
