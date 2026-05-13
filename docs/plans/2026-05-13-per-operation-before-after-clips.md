# Development Plan: Per-operation Before/After Clips

## Why
Per-operation removed clips show what will be cut, but reviewers also need short context clips around each edit to decide whether the edit sounds natural.

## SDD scope
- During `write_preview`, generate `preview/operations/<operation_id>/before-after.mp3` for each operation source range.
- Use configurable fixed context padding for now (2 seconds), clipped at zero.
- Keep aggregate and per-operation removed previews intact.
- Keep FFmpeg-gated behavior and metadata-first failure behavior.

## TDD acceptance criteria
1. `write_preview` invokes one FFmpeg command per operation for before/after context preview.
2. The command uses `-ss` and `-t` based on source range ± 2 seconds.
3. Existing per-operation removed and aggregate previews still run.
4. Full uv tests and compileall pass.
