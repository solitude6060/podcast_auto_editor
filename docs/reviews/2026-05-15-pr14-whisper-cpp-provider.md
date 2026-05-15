# PR 14 Review: Optional whisper.cpp ASR provider

Date: 2026-05-15
PR: https://github.com/solitude6060/podcast_auto_editor/pull/14
Branch: `feature/whisper-cpp-provider` → `dev`

## Review scope

- Optional local ASR provider boundary for `whisper-cpp-local`.
- CLI option forwarding for local binary/model/language/thread settings.
- Transcript validation-before-write safety.
- Local-first RTX 4090 resource profile and user-facing docs.

## Findings

| Finding | Severity | Resolution |
| --- | --- | --- |
| Required-path validation must fail before writing transcript output. | High | Covered by `test_whisper_cpp_provider_requires_binary_and_model_without_writing`. |
| Invalid provider JSON must not create a final transcript file. | High | Covered by `test_whisper_cpp_provider_rejects_invalid_json_without_writing`. |
| Provider must remain optional with no new dependency or vendored model. | Medium | Implementation shells out only when explicitly selected and adds no dependencies. |
| User-facing docs require Traditional Chinese coverage. | Medium | Added `README.zh-TW.md` section and zh-TW plan. |

## Verification evidence

Local:

- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_asr.py -p no:cacheprovider` → `15 passed in 0.07s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_asr.py tests/test_ai_resources.py tests/test_cli.py -p no:cacheprovider` → `53 passed in 0.20s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `147 passed in 2.47s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- `git diff --check` → passed.
- `git ls-files .omx` → no tracked `.omx` files.
- Recent commit trailer grep for `Co-authored-by` → no matches.

CI:

- GitHub Actions CI run `25893190612` → success.

## Decision

Approved for merge into `dev`.
