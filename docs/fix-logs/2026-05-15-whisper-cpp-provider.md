# Fix Log: Optional whisper.cpp local ASR provider

Date: 2026-05-15
Branch: `feature/whisper-cpp-provider`

## Prompt-to-artifact checklist

- User goal: continue local-first AI development for podcast auto editing on an RTX 4090 workstation.
- Planning artifact: `docs/plans/2026-05-15-whisper-cpp-provider.md`
- Traditional Chinese planning artifact: `docs/plans/2026-05-15-whisper-cpp-provider.zh-TW.md`
- TDD tests: `tests/test_asr.py`, `tests/test_ai_resources.py`
- Implementation: `podcast_auto_editor/asr.py`, `podcast_auto_editor/cli.py`, `podcast_auto_editor/ai_resources.py`
- User-facing docs: `README.md`, `README.zh-TW.md`

## TDD evidence

1. Added failing tests for provider registration, missing required paths, JSON parsing, invalid JSON handling, CLI option forwarding, and AI profile fallback naming.
2. Confirmed expected red state:
   - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_asr.py -p no:cacheprovider`
   - Result: `5 failed, 10 passed`
   - Cause: provider was not registered and CLI did not recognize `--binary`, `--model-path`, `--language`, or `--threads`.
3. Implemented `WhisperCppLocalProvider` and CLI option forwarding.
4. Confirmed targeted green state:
   - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_asr.py -p no:cacheprovider`
   - Result: `15 passed in 0.07s`
5. Confirmed feature-adjacent green state:
   - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_asr.py tests/test_ai_resources.py tests/test_cli.py -p no:cacheprovider`
   - Result: `53 passed in 0.20s`

## Changes

- Added optional `whisper-cpp-local` provider that shells out to a user-managed local `whisper.cpp` executable.
- Required explicit `--binary` and `--model-path` before execution.
- Parsed `whisper.cpp` JSON shapes using `transcription[].offsets`, `segments[].start/end`, or `segments[].t0/t1`.
- Preserved transcript validation before write via the existing `transcribe_to_file` path.
- Added CLI flags for binary/model/language/thread selection.
- Updated RTX 4090 resource profile to name the local `whisper-cpp-local` fallback.
- Documented usage in English and Traditional Chinese README sections.

## Deferred / not changed

- No vendored `whisper.cpp` binary or model files.
- No new Python dependencies.
- No cloud ASR integration; MiniMax remains fallback-only documentation.

## Final verification evidence

- Full tests: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `147 passed in 2.47s`.
- Syntax/import check: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- Diff whitespace: `git diff --check` → passed.
- Local-only hygiene: `git ls-files .omx` → no tracked `.omx` files.
- Co-author hygiene: `git log --format='%h %s%n%b' -20 | grep -i 'Co-authored-by' || true` → no matches.
