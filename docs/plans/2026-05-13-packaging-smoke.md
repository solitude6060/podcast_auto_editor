# Next Development Plan: Packaging and Smoke Verification

## Why
A local-first CLI MVP should be easy to validate after a fresh clone. The repo already uses uv and demo fixtures; the next polish step is a single smoke-test script that exercises the CLI without publishing or requiring cloud services.

## SDD scope
- Add a stdlib smoke-test script under `scripts/`.
- The script must run `uv` pytest/compileall and a CLI help smoke path.
- If FFmpeg is present, optionally generate demo fixtures; if absent, skip fixture generation clearly.
- Document uv sync/test/smoke usage.

## TDD acceptance criteria
1. Smoke script exists and is documented.
2. Smoke script can run in this repo with uv and exits 0.
3. Full uv tests and compileall pass.
