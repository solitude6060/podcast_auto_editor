# PR 6 Review — ASR stub provider boundary

## Scope reviewed
- Branch: `feature/asr-stub-provider`
- Target: `dev`
- Feature: advanced roadmap Phase A3 optional local ASR adapter boundary.

## Prompt-to-artifact checklist
| Requirement | Evidence |
| --- | --- |
| Continue planned development | `docs/plans/2026-05-14-asr-stub-provider.md` implements advanced Phase A3. |
| SDD/TDD with plan files | Plan and zh-TW plan exist; `tests/test_asr.py` was written first and initially failed because `asr.py` did not exist. |
| Provider protocol and registry | `podcast_auto_editor/asr.py` defines `TranscriptProvider`, registry helpers, and `StubTranscriptProvider`. |
| `transcribe` CLI with provider selection | `podcast_auto_editor/cli.py` adds `transcribe <input> --provider stub --out <path>`. |
| Deterministic stub provider | `tests/test_asr.py::test_stub_provider_returns_valid_transcript_segments`. |
| Existing transcript validation reused | `transcribe()` uses `normalize_transcript_segments()` before writing. |
| ASR failure never mutates media/output | Unknown and invalid provider tests assert output file is not written. |
| No mandatory ASR dependencies | `pyproject.toml` unchanged; core tests run without ASR packages. |
| Traditional Chinese docs | `README.zh-TW.md`, `docs/plans/2026-05-14-asr-stub-provider.zh-TW.md`. |
| `.omx` local-only | `git ls-files .omx` produced no output. |
| No co-author trailers | Recent `git log` scan produced no `Co-authored-by` output. |

## Findings
No blocking findings. One implementation issue was caught during TDD: argparse `choices` returned exit code 2 before the ASR registry could report actionable provider errors. It was fixed before review by routing provider validation through `ASRProviderError`.

## Verification evidence
- Targeted ASR/transcript/CLI tests: `41 passed`.
- Full regression: `124 passed in 2.33s`.
- Compileall: `uv run python -m compileall -q podcast_auto_editor tests` passed.
- CLI smoke: `uv run python -m podcast_auto_editor transcribe demo.wav --provider stub --out /tmp/podcast-asr-smoke/transcript.json` wrote `transcript.v1` JSON.
- Diff hygiene: `git diff --check` passed.
- GitHub Actions PR #6 run `25842474454` passed.
- Local-only hygiene: `git ls-files .omx` produced no tracked files.
- Commit hygiene: no recent `Co-authored-by` trailers detected.

## Verdict
APPROVED for merge into `dev`.
