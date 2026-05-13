# Next Development Plan: Quality Gate Hardening

## Why
Publishable quality is an MVP requirement. Render currently records quality gate reports but should also fail clearly when required gates fail, instead of allowing a successful render path with failed quality metadata.

## SDD scope
- Make render fail when required audio or A/V quality gates fail.
- Preserve quality metadata on the in-memory timeline before raising, where possible.
- Keep diagnostic errors clear and actionable.

## TDD acceptance criteria
1. `render` raises `MediaToolError` when loudness/true-peak/clipping quality gates fail.
2. Existing successful FFmpeg acceptance path remains green.
3. Full uv tests and compileall pass.
