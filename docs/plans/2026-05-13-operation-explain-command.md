# Operation explain command increment

## Goal
Start Phase A4 rich edit explainability with a deterministic explanation model and CLI command for a single timeline operation.

## Acceptance criteria
- `podcast-auto-editor explain <timeline> --operation-id <id>` explains one operation without needing media files.
- JSON output includes operation id/type/state, detector, reason code, evidence text, confidence, risk, required review path, and artifact refs.
- Markdown output is readable for producer review and includes the same critical trust fields.
- Missing operation ids fail with a clear non-zero CLI error.
- Tests are written before implementation and run under uv.

## Files
- `podcast_auto_editor/explain.py` — explainability model and formatters.
- `podcast_auto_editor/cli.py` — parser entry and command handling.
- `tests/test_explain.py` — model and formatting tests.
- `tests/test_cli.py` — CLI command tests.
- `docs/sdd/podcast-auto-editor-mvp.md` and fix log for traceability.

## Verification
- Targeted red/green tests for explain model and CLI.
- Full `uv run --group dev pytest -q -p no:cacheprovider`.
- `uv run python -m compileall -q podcast_auto_editor tests`.
