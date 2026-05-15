# PR 16 Review: Docker Compose local AI stack

Date: 2026-05-15
PR: https://github.com/solitude6060/podcast_auto_editor/pull/16
Branch: `feature/validate-run-command` → `dev`

## Review scope

- Docker Compose app + optional local AI service.
- GPU reservation and localhost-only exposure.
- Local-only model/secret/run/.omx hygiene.
- `validate-run` preflight for config/timeline/transcript duration validation.
- English and Traditional Chinese user docs.

## Findings

| Finding | Severity | Resolution |
| --- | --- | --- |
| AI service must not expose a network API broadly by default. | High | `ollama` port is bound to `127.0.0.1:11434`. |
| GPU configuration should follow current Compose device reservation shape. | Medium | Uses `deploy.resources.reservations.devices` with `driver: nvidia` and `capabilities: [gpu]`. |
| Secrets and model files must stay out of git. | High | `.env`, models, runs, and `.omx` are ignored; tests assert no secret sample value. |
| User-facing docs need Traditional Chinese coverage. | Medium | Added README.zh-TW updates and `docs/docker-compose-ai-stack.zh-TW.md`. |

## Verification evidence

Local:

- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_cli.py tests/test_docker_compose.py -p no:cacheprovider` → `38 passed in 0.18s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `155 passed in 2.68s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- `docker compose --profile ai config` → passed.
- `git diff --check` → passed.
- `git ls-files .omx` → no tracked `.omx` files.
- Recent commit trailer grep for `Co-authored-by` → no matches.

CI:

- GitHub Actions CI run `25893680965` → success.

## Decision

Approved for merge into `dev`.
