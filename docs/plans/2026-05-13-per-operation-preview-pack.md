# Development Plan: Per-operation Preview Pack

## Why
Current preview artifacts include one removed-segments preview for all operations. Producers need per-operation preview references to review each proposed speech/silence edit safely.

## SDD scope
- Generate stable per-operation preview metadata paths under `preview/operations/<operation_id>/`.
- Provide before/after context and removed-audio preview refs per operation.
- Attach these refs to each operation without changing timeline schema version.
- Keep actual FFmpeg clip generation gated and deterministic.

## TDD acceptance criteria
1. Preview metadata contains per-operation preview refs for each operation with source ranges.
2. Operations receive `preview_ref` pointing to their per-operation before/after preview when refs are attached.
3. Existing aggregate preview behavior remains compatible.
4. Full uv tests and compileall pass.
