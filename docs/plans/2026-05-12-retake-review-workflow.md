# Next Development Plan: Explicit Retake Review Workflow

## Why
The MVP correctly refuses unsafe bulk acceptance of `retake_cut` operations, but the CLI currently has no safe human-review path for intentionally accepting a specific retake. `render` even references a future explicit review command. The next increment should close that workflow gap without weakening AI safety defaults.

## SDD scope
- Add an explicit CLI review acceptance path for selected operations.
- Only selected operation IDs may be reviewed; no bulk retake acceptance.
- Reviewed acceptance must record provenance with reviewer, note, timestamp, and policy marker.
- Render may accept `retake_cut` only if it has either successful auto-accept provenance or explicit manual-review provenance.
- Rejected reviewed operations remain out of recovery/cut lists.

## TDD acceptance criteria
1. A proposed `retake_cut` can be accepted through a review command and receives preview/diff/recovery refs.
2. Reviewed retake provenance is sufficient for render safety validation.
3. The review command refuses bulk acceptance when no `--operation-id` is provided.
4. Ordinary `accept` remains insufficient for retake render approval.
5. Existing uv test suite and compileall pass.

## Implementation notes
- Keep media rendering unchanged.
- Prefer a small helper in `pipeline.py` reused by CLI.
- Keep timeline schema `timeline.v1`; encode review data in operation `provenance`.
