# Plan: Docker Compose local AI stack

Date: 2026-05-15
Branch: `feature/validate-run-command`

## Goal

Add a Docker Compose development/runtime stack that can run the podcast editor app plus a local RTX 4090 AI service without making cloud APIs or model files part of the repository.

## Constraints

- Keep the project local-first and no-cloud by default.
- Use Docker Compose GPU reservations for the local LLM service.
- Keep MiniMax as environment-configured fallback only; no key values in repo.
- Do not commit model weights, generated runs, `.omx`, or credentials.
- Keep app dependencies uv-managed.
- Keep `whisper.cpp` and GGML models user-mounted optional paths, not image contents.

## Compose services

- `app`: local development/runtime container for `podcast_auto_editor`, uv, source mounts, run artifacts, and optional model mounts.
- `ollama`: optional local GPU LLM service for RTX 4090 workflows, exposed only on localhost.

## Acceptance criteria

- `compose.yaml` defines app and local AI service with GPU reservation for NVIDIA.
- `.env.example` documents safe local variables without secrets.
- Dockerfile uses uv and does not vendor models.
- Docker docs exist in English and Traditional Chinese.
- Tests verify compose safety constraints without needing Docker daemon access.
