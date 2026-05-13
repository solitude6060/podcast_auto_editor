# Next Development Plan: Video Sync Hardening

## Why
Optional MP4 support must fail safely when source media lacks measurable stream durations or starts already out of sync. The current implementation primarily checks post-render output, so bad source metadata may fail late or opaquely.

## SDD scope
- Add reusable source A/V sync validation from timeline tracks before MP4 render.
- Fail before `render_video` when source audio/video durations are missing or drift exceeds tolerance.
- Extend A/V sync reports with measured audio/video durations for diagnostics.

## TDD acceptance criteria
1. Source sync validation fails on missing stream durations.
2. Source sync validation fails on source drift above configured tolerance.
3. Render raises before calling `render_video` when source validation fails.
4. `measure_av_sync` report includes audio/video durations when measurable.
5. Full uv tests and compileall pass.
