# Optional local ASR adapter stub implementation log

## Scope
Implemented advanced roadmap Phase A3 with a dependency-free transcript provider boundary and deterministic stub provider.

## Changes
- Added `podcast_auto_editor/asr.py` with provider protocol, registry, stub provider, validation, and safe file writing.
- Added `transcribe <input> --provider stub --out <transcript.json>` CLI command.
- Provider output is normalized through existing transcript validation before output is written.
- Unknown or invalid providers fail without writing the output transcript file.
- Updated English and Traditional Chinese README usage docs.

## TDD evidence
- Wrote `tests/test_asr.py` first.
- Initial targeted run failed because `podcast_auto_editor.asr` did not exist.
- After implementation, one CLI test exposed overly strict argparse provider choices; fixed so provider selection errors use the ASR registry path and return code 1.

## Verification
- Targeted ASR tests: `6 passed`.
- Targeted ASR/transcript/CLI tests: `41 passed`.
- Full regression: `124 passed in 2.33s`.
- Compileall: `uv run python -m compileall -q podcast_auto_editor tests` passed.
- Diff hygiene: `git diff --check` passed.
- Local-only hygiene: `git ls-files .omx` produced no tracked files.
- Commit hygiene: no recent `Co-authored-by` trailers detected.
