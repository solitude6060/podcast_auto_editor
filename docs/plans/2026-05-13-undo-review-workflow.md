# Next Development Plan: Explicit Undo Workflow

## Why
The MVP writes recovery artifacts and undo instructions, but users still need a safe CLI path to turn accepted edits back into proposed edits before re-rendering. Without this, reversibility is documented but not directly operable.

## SDD scope
- Add an explicit `undo` CLI command for accepted timeline operations.
- Require either selected `--operation-id` values or `--all`; no implicit bulk mutation.
- Only accepted operations may be undone; proposed/rejected operations are left unchanged unless explicitly selected, in which case the command should fail clearly.
- Rebuild `recovery` after undo so source/output maps match the new accepted set.
- Record undo provenance on each operation for auditability.

## TDD acceptance criteria
1. Selected accepted operation can be restored to `proposed` and removed from recovery removed segments.
2. `--all` restores all accepted operations while preserving rejected operations.
3. CLI refuses `undo` without `--operation-id` or `--all`.
4. CLI refuses selected operation IDs that are not currently accepted.
5. Full uv tests and compileall pass before commit/push.
