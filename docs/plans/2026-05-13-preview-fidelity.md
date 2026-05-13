# Next Development Plan: Preview Fidelity

## Why
Preview artifacts should support producer decisions. The existing removed-segments preview was a generic source excerpt, not a preview of the segments that would be removed.

## SDD scope
- Generate `removed-segments-preview.mp3` from the timeline operation source ranges.
- Keep `before-after-preview.mp3` as a quick source-context preview for now.
- Preserve preview metadata in `waveform.json`.
- Keep behavior deterministic and FFmpeg-gated.

## TDD acceptance criteria
1. `write_preview` invokes FFmpeg with an `aselect` expression over operation source ranges for removed-segments preview.
2. Missing input still writes waveform/preview metadata before failing clearly.
3. Full uv tests and compileall pass.
