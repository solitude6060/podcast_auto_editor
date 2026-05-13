# Development Plan: Per-operation Removed Clips

## Why
The previous A2 increment added stable per-operation preview refs. The next step is to generate the per-operation removed-audio clip for each operation so reviewers can inspect individual cuts, not just aggregate removed audio.

## SDD scope
- During `write_preview`, generate `preview/operations/<operation_id>/removed.mp3` for each operation source range.
- Keep aggregate removed-segments preview behavior intact.
- Use FFmpeg only when input exists and FFmpeg is available.
- Continue writing metadata before media generation errors.

## TDD acceptance criteria
1. `write_preview` invokes one FFmpeg command per operation to create that operation's removed clip.
2. Per-operation command uses the operation's exact source range via `aselect`.
3. Aggregate removed preview command still runs.
4. Full uv tests and compileall pass.
