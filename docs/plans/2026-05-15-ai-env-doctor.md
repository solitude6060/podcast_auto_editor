# Plan: AI environment doctor

Date: 2026-05-15
Branch: `feature/ai-env-doctor`

## Goal

Add a read-only `ai doctor` command that helps users verify their local RTX 4090 AI environment after the Docker Compose stack exists. The command should report safe, actionable status for Docker Compose files, optional Ollama connectivity, optional `whisper.cpp` binary/model paths, and MiniMax fallback configuration without leaking secrets.

## Constraints

- Read-only diagnostics only; do not download models or call non-local APIs.
- MiniMax remains fallback-only and secret values must be redacted.
- Use only Python standard library.
- The command must work without Docker daemon access; Compose file checks should be static.
- JSON and Markdown outputs are required for scriptable and human-readable diagnostics.
- Traditional Chinese user-facing docs must be updated.

## CLI contract

```bash
uv run python -m podcast_auto_editor ai doctor --format markdown
uv run python -m podcast_auto_editor ai doctor --format json
```

Optional checks:

```bash
uv run python -m podcast_auto_editor ai doctor \
  --compose-file compose.yaml \
  --ollama-url http://127.0.0.1:11434 \
  --whisper-binary /path/to/whisper-cli \
  --whisper-model /models/ggml-large-v3-q5_0.bin
```

## Acceptance criteria

- Reports `ok`, `warning`, or `missing` checks with actionable messages.
- Static Compose check verifies local AI service and GPU reservation hints.
- Ollama check is optional and timeout-bounded.
- whisper.cpp binary/model checks are optional path existence checks.
- MiniMax check reports whether the env var is configured without printing its value.
- CLI exits 0 when all checks are ok/warning and exits 1 when required local artifacts are missing.
