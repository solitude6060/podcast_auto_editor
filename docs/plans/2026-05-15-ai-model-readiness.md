# Plan: AI model readiness report

Date: 2026-05-15
Branch: `feature/ai-model-readiness`

## Goal

Add a lightweight `ai models --readiness` mode that compares the local model catalog against an Ollama `/api/tags` response so users can see which smoke/recommended/heavy models are already installed without downloading models or running GPU inference.

## Constraints

- Read-only only: no model downloads and no inference.
- Timeout-bounded Ollama request; offline mode accepts a saved tags JSON fixture.
- Keep smoke tier useful while GPU is shared with other projects.
- JSON and Markdown outputs.
- Traditional Chinese user docs update.

## Acceptance criteria

- Readiness report lists catalog models with `installed` true/false.
- Offline `--ollama-tags-json` works without network or Docker.
- Live `--ollama-url` is timeout-bounded and reports warning on connection failure.
- CLI returns 0 for reachable/offline reports, and does not treat missing models as a process error.
