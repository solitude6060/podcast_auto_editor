# Optional faster-whisper local ASR provider implementation log

## Scope
Implemented the first real RTX 4090 local ASR adapter boundary with `faster-whisper-local`, while keeping core tests dependency-free.

## Changes
- Added `FasterWhisperLocalProvider` to `podcast_auto_editor/asr.py`.
- Registered provider name `faster-whisper-local` alongside `stub`.
- Added `transcribe` CLI options: `--model`, `--device`, and `--compute-type`.
- Missing optional `faster_whisper` dependency raises a clear `ASRProviderError` before writing output.
- Provider output is normalized and validated through existing `transcript.v1` validation before writing.
- Updated English and Traditional Chinese README usage docs.

## TDD evidence
- Added failing tests to `tests/test_asr.py` before implementation.
- Initial targeted run failed because `faster-whisper-local` was not registered and CLI options did not exist.
- Implemented provider and CLI options until targeted tests passed.

## Verification
- Targeted ASR tests: `10 passed`.
- Targeted ASR/AI resource/CLI tests: `48 passed`.
- Full regression: `142 passed in 2.53s`.
- Compileall: `uv run python -m compileall -q podcast_auto_editor tests` passed.
- Diff hygiene: `git diff --check` passed.
- Local-only hygiene: `git ls-files .omx` produced no tracked files.
- Commit hygiene: no recent `Co-authored-by` trailers detected.
