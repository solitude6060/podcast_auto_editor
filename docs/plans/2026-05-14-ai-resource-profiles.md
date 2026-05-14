# AI resource profiles for RTX 4090 local-first operation

## Goal
Codify the AI resource plan for a single RTX 4090 workstation so future ASR/LLM/music/image adapters have a safe default: local-first, 24GB VRAM-aware, and MiniMax only as an explicit non-local fallback.

## Scope
- Add repository-native AI resource profile definitions for `rtx4090-local` and `minimax-fallback`.
- Add CLI command to inspect profiles as JSON or Markdown.
- Keep `rtx4090-local` as the default profile.
- Mark MiniMax as non-local, fallback-only, and never enabled implicitly.
- Document English and Traditional Chinese usage.

## Acceptance criteria
- `ai resources --format json` returns all profiles with default profile metadata.
- `rtx4090-local` includes local ASR/LLM/music/image roles sized for 24GB VRAM operation.
- `minimax-fallback` is marked `local=false`, `fallback_only=true`, and does not appear as default.
- Unknown profile names fail clearly.
- No API keys, secrets, or cloud credentials are stored.
- Full uv pytest and compileall pass.
