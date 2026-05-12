# Transcript Time Remap Increment

## Prompt-to-artifact checklist
- Continue planning and development → `docs/plans/2026-05-12-transcript-time-remap.md`.
- Keep transcript/subtitle/chapter outputs publishable → `remap_cues_to_output` maps source transcript cues through `recovery.source_to_output`.
- Preserve SDD/TDD discipline → tests were added before implementation and initially failed on missing helper import.
- Avoid schema churn → implementation reuses existing `timeline.v1` recovery map.
- Keep uv environment → verification uses `uv run --group dev`.

## Verification evidence
- Initial targeted test run failed on missing `remap_cues_to_output`, confirming red TDD state.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_artifacts_subtitles_pipeline.py -p no:cacheprovider` → 9 passed.

## Notes
Cues after cuts shift earlier, cues fully inside removed ranges are dropped, and cues spanning cuts are split across kept output ranges with the same text.
