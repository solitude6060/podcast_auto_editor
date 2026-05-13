# Static HTML report increment

## Goal
Implement Phase A7's local-only static HTML report so producers can open a run directory in a browser and review operation summaries, preview links, export profiles, warnings, and recovery artifacts without running a server.

## Acceptance criteria
- `podcast-auto-editor report <run_dir> --format html` prints a complete static HTML document.
- `podcast-auto-editor html-report <run_dir> --out <file>` writes the same HTML to disk.
- HTML escapes dynamic timeline/report values.
- Links are local relative paths to preview/diff/recovery/export artifacts.
- Tests cover HTML content, escaping, and CLI write path.

## Files
- `podcast_auto_editor/html_report.py`
- `podcast_auto_editor/cli.py`
- `tests/test_html_report.py`
- `tests/test_cli.py`
