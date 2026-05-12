# Next Development Plan: Transcript and Subtitle Time Remapping

## Why
The MVP can emit transcript/subtitle/chapter files, but supplied transcript cues are currently written with source-media timestamps. Once silence or retake cuts are accepted, post-edit subtitles must use output-media timestamps or they will drift after the first cut.

## SDD scope
- Add deterministic cue remapping from source timeline to edited output timeline using `recovery.source_to_output`.
- Drop cues that fall entirely inside removed ranges.
- Preserve cue text and split cues only when a cue intersects multiple kept ranges.
- Keep empty/no-cut timelines unchanged.
- Reuse existing `timeline.v1` recovery map; no schema bump.

## TDD acceptance criteria
1. Cues after an accepted cut shift earlier by the removed duration.
2. Cues entirely inside removed segments are dropped.
3. Cues spanning a cut are split into kept output ranges.
4. `transcribe_and_write` writes remapped transcript/SRT/VTT timings.
5. Full uv test suite and compileall pass.
