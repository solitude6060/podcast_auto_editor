# Optional faster-whisper local ASR provider

## Goal
Implement the first real RTX 4090 local ASR adapter while preserving the zero-dependency core: `faster-whisper-local` should be available only when the optional `faster_whisper` package and local model are installed.

## Scope
- Add `FasterWhisperLocalProvider` behind optional import.
- Register provider name `faster-whisper-local` alongside `stub`.
- Add CLI options for ASR model, device, and compute type.
- Keep `stub` as deterministic default for tests; do not add mandatory dependencies to `pyproject.toml`.
- Validate all provider output as `transcript.v1` before writing.
- Document English and Traditional Chinese usage and 4090 settings.

## Acceptance criteria
- Missing `faster_whisper` dependency fails clearly and does not write output.
- Mocked faster-whisper module produces normalized transcript segments.
- CLI passes `--model`, `--device`, and `--compute-type` to the provider.
- Core full test suite passes without installing faster-whisper.
- MiniMax remains fallback-only and is not involved in default ASR selection.
