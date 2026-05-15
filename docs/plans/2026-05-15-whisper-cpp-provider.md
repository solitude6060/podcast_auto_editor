# Plan: Optional whisper.cpp local ASR provider

Date: 2026-05-15
Branch: `feature/whisper-cpp-provider`

## Goal

Add an optional `whisper-cpp-local` transcript provider so the RTX 4090 local-first profile has a dependency-light ASR fallback path that can use a user-managed `whisper.cpp` executable and GGML model file.

## Constraints

- Keep `stub` as the deterministic default provider for tests and smoke checks.
- Do not add `whisper.cpp` or model files as Python dependencies or repository artifacts.
- Require explicit local `--binary` and `--model-path` inputs before execution.
- Validate provider output as `transcript.v1` before writing any transcript file.
- Keep MiniMax as a documented non-local fallback only, never an implicit ASR runtime dependency.
- Preserve uv-managed verification and no `.omx` tracking.

## CLI contract

```bash
uv run python -m podcast_auto_editor transcribe input.wav \
  --provider whisper-cpp-local \
  --binary /path/to/whisper-cli \
  --model-path /models/ggml-large-v3-q5_0.bin \
  --language zh \
  --threads 8 \
  --out transcript.json
```

## Acceptance criteria

- `provider_names()` includes `whisper-cpp-local`.
- Missing `--binary` or `--model-path` fails clearly and does not write output.
- Missing local files fail clearly before running the external executable.
- Valid `whisper.cpp` JSON output is converted into normalized transcript segments.
- Invalid JSON or invalid segment shape fails clearly and does not write output.
- CLI forwards `--binary`, `--model-path`, `--language`, and `--threads` to the provider.
- English and Traditional Chinese README sections document optional usage.
- Targeted and full uv test suites pass.

## TDD plan

1. Add failing provider/CLI tests for registration, missing inputs, JSON parsing, invalid JSON, and option forwarding.
2. Implement the smallest provider adapter and CLI options to pass those tests.
3. Add docs and fix log.
4. Run targeted tests, full tests, compileall, diff hygiene, `.omx` tracking check, and co-author trailer check.
