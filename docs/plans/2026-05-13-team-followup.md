# Team Follow-up Development Plan

## Why
The next phase was delegated to OMX team lanes to continue the MVP after retake review and transcript time remapping. The leader must integrate lane outputs conservatively, resolve conflicts, and preserve SDD/TDD/uv/git hygiene.

## Lanes
1. Transcript import: validate transcript JSON before pipeline execution.
2. Preview/diff UX: enrich human-readable diff and removed-segment preview metadata.
3. Media fixtures: add deterministic demo fixture generation when ffmpeg is available.
4. QA/docs: keep README, SDD, tests, and verification evidence current.

## Acceptance criteria
- Transcript JSON supports legacy segment arrays and `transcript.v1` wrappers.
- Invalid transcript JSON fails before media pipeline execution.
- Diff artifacts include richer removed segment metadata and human-readable tables.
- Demo fixtures can be generated from CLI with clear ffmpeg dependency behavior.
- Full uv test suite and compileall pass.
- `.omx/` remains untracked and ignored.
