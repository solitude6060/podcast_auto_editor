# AI resource profiles implementation log

## Scope
Codified a local-first RTX 4090 AI resource plan with MiniMax as explicit non-local fallback only.

## Changes
- Added `podcast_auto_editor/ai_resources.py` with `rtx4090-local` and `minimax-fallback` profiles.
- Added `ai resources` CLI command with JSON and Markdown output.
- Kept `rtx4090-local` as default and marked MiniMax as `fallback_only`, `local=false`, and `default_enabled=false`.
- Updated English and Traditional Chinese README docs.

## TDD evidence
- Wrote `tests/test_ai_resources.py` before implementation.
- Initial targeted run failed because `podcast_auto_editor.ai_resources` did not exist.
- Implemented profile module and CLI integration until targeted tests passed.

## Verification
- Targeted AI resource tests: `8 passed`.
- Targeted AI resource/ASR/CLI tests: `44 passed`.
- Full regression: `138 passed in 2.43s`.
- Compileall: `uv run python -m compileall -q podcast_auto_editor tests` passed.
- Diff hygiene: `git diff --check` passed.
- Local-only hygiene: `git ls-files .omx` produced no tracked files.
- Commit hygiene: no recent `Co-authored-by` trailers detected.
