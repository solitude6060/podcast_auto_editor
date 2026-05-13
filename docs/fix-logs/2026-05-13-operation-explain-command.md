# Operation explain command implementation log

## Scope
Phase A4 rich edit explainability first increment: explain one timeline operation without requiring media files and enrich reports with operation grouping by risk/detector.

## Changes
- Added `podcast_auto_editor/explain.py` with deterministic operation explanation payloads.
- Added `podcast-auto-editor explain <timeline> --operation-id <id>` with Markdown and JSON formats.
- Speech-changing operations expose detector, reason code, evidence text, confidence, risk, required review path, and artifact refs.
- Deterministic silence cuts are marked `safe_default_review_optional`.
- Existing report output now includes operation grouping by risk and detector.

## Verification
- Targeted red tests failed before implementation because `podcast_auto_editor.explain` and CLI command were missing.
- Targeted green: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_cli.py::test_report_cli_outputs_json_and_markdown tests/test_explain.py tests/test_cli.py::test_explain_cli_outputs_json_for_operation tests/test_cli.py::test_explain_cli_reports_missing_operation -p no:cacheprovider` → `7 passed`.
