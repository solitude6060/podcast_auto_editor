# Project and batch dry-run workflow

## Goal
Implement advanced roadmap Phase A1: local project manifests and batch dry-run reports for multiple podcast episodes without adding cloud collaboration or publishing/upload behavior.

## Scope
- Add `project init <project_dir>` to create a local `podcast-project.v1.json` manifest outside `.omx`.
- Add `batch dry-run <inputs...>` to run inspectable dry-runs for multiple input files.
- Continue processing unrelated episodes when one fails, unless `--fail-fast` is passed.
- Write aggregate JSON and Markdown reports with episode status, warnings, removed duration, and quality state.

## Acceptance criteria
- Batch dry-run never writes edited media exports; it reuses the existing dry-run artifact path.
- Failed episodes are recorded in the aggregate report and do not stop later episodes unless `--fail-fast` is set.
- Aggregate report is available as both JSON and Markdown.
- User-facing README documentation has Traditional Chinese coverage.
- Full uv pytest and compileall pass.
