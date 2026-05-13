# Next Development Plan: Safe Speech Cleanup Proposals

## Why
The MVP needs low-risk mistake/retake assistance without unsafe automatic speech deletion. Existing retake heuristics cover repeated takes; the next narrow step is to propose filler/false-start cleanup candidates while keeping them manual-review only.

## SDD scope
- Detect conservative filler/false-start transcript segments as `speech_cut` operations.
- All `speech_cut` operations default to `proposed` and are never accepted by safe defaults.
- `review-accept` may manually accept selected `speech_cut` operations with provenance.
- Render may cut accepted `speech_cut` operations only with explicit manual review provenance.

## TDD acceptance criteria
1. Filler/false-start transcript segments create proposed `speech_cut` operations with explanatory provenance.
2. Safe defaults do not accept `speech_cut` operations.
3. `review-accept` can accept a selected `speech_cut` and records manual review provenance.
4. Render safety rejects accepted `speech_cut` without manual review provenance.
5. Full uv tests and compileall pass.
