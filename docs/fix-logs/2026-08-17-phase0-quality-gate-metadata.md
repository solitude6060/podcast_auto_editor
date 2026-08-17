# Fix log: Phase 0 quality-gate metadata

Date: 2026-08-17  
Review: `docs/reviews/2026-08-17-phase0-status-sync.md`  
Branch: `docs/2026-08-17-status-sync`

## F1 — top-level gate stayed on the first profile

**Repro:** `tests/test_exports.py::test_render_quality_failure_names_profile` after changing the assertion to expect the failed profile. Archive WAV passed, `podcast-stereo` failed loudness, `export_metadata.quality_gate_report.passed` was still `true`.

**Fix:** On quality failure, assign `quality_gate_report` to the current (failed) `gate_report`. Success path still keeps the first profile as the top-level report and `edited_audio`.

**Tests:** `tests/test_exports.py::test_render_quality_failure_names_profile`, `tests/test_cli.py::test_report_cli_surfaces_profile_quality_details`

## F2 — failed metadata never reached the report file

**Repro:** `tests/test_cli.py::test_render_cli_writes_failed_quality_metadata`. `render` raised `MediaToolError`; CLI did not catch it; `timeline.accepted.v1.json` was not written.

**Fix:** CLI `render` catches `MediaToolError`, writes the mutated timeline, prints the error, returns 1. `run_pipeline` writes the accepted timeline before re-raising. CLI `run` catches `MediaToolError` and returns 1.

**Tests:** `tests/test_cli.py::test_render_cli_writes_failed_quality_metadata`

## F3 — restored assertion

Restored `operation_explanations[0]["operation_known"]` in `tests/test_ai_drafts.py::test_generate_ai_draft_normalizes_live_response`.

## Deferred

- F4: wrap incomplete loudnorm JSON as `MediaToolError` (same pattern as `measure_audio_quality`).
