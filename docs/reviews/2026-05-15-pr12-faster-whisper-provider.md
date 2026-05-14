# PR 12 Review — Optional faster-whisper ASR provider

## Scope reviewed
- Branch: `feature/faster-whisper-provider`
- Target: `dev`
- Feature: optional `faster-whisper-local` ASR provider for RTX 4090 local profile.

## Prompt-to-artifact checklist
| Requirement | Evidence |
| --- | --- |
| Real local ASR adapter path | `FasterWhisperLocalProvider` registered as `faster-whisper-local`. |
| Keep core dependency-free | `pyproject.toml` unchanged; missing dependency path is tested and fails before write. |
| 4090-oriented options | CLI accepts `--model`, `--device`, and `--compute-type`; docs show `large-v3`, `cuda`, `float16`. |
| Validate before write | Provider output flows through `normalize_transcript_segments()` via `transcribe()`. |
| Missing dependency does not write output | `test_faster_whisper_provider_missing_dependency_does_not_write`. |
| Mocked provider output normalizes | `test_faster_whisper_provider_normalizes_segments`. |
| Traditional Chinese docs | `README.zh-TW.md`, `docs/plans/2026-05-15-faster-whisper-provider.zh-TW.md`. |
| MiniMax remains fallback-only | No MiniMax runtime changes; default provider remains `stub`. |
| `.omx` local-only | `git ls-files .omx` produced no output. |
| No co-author trailers | Recent `git log` scan produced no `Co-authored-by` output. |

## Findings
No blocking findings. The adapter is optional, explicitly selected, and failure-safe when `faster_whisper` is not installed.

## Verification evidence
- Targeted ASR/AI resource/CLI tests: `48 passed`.
- Full regression: `142 passed in 2.53s`.
- Compileall: `uv run python -m compileall -q podcast_auto_editor tests` passed.
- CLI missing-dependency smoke: `faster-whisper-local` reports optional package requirement before writing output.
- Diff hygiene: `git diff --check` passed.
- GitHub Actions PR #12 run `25875538437` passed.
- Local-only hygiene: `git ls-files .omx` produced no tracked files.
- Commit hygiene: no recent `Co-authored-by` trailers detected.

## Verdict
APPROVED for merge into `dev`.
