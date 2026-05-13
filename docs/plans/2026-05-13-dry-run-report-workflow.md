# Next Development Plan: Dry-run and Report Workflow

## Why
Producers need to inspect proposed/accepted changes and warnings before committing to a media render. The current `run` command renders immediately; artifact inspection exists but is tied to render-side workflow.

## SDD scope
- Add `dry-run` CLI that probes/analyzes/transcript-detects and writes proposed timeline, accepted safe-default timeline, diff, recovery, preview metadata, derived transcript/subtitle/chapter assets, and manifest without rendering media exports.
- Dry-run must not write `exports/episode.edited.*` media files.
- Add `report` CLI that reads a run directory and emits Markdown or JSON summary for producers.
- Report must include operation counts, total removed duration, quality status when present, derived asset paths, and warnings.

## TDD acceptance criteria
1. `dry-run` creates proposed/accepted timelines, diff, recovery, preview metadata, transcript/subtitle/chapter assets, and manifest without edited WAV/MP4 exports.
2. `report --format json` returns machine-readable operation counts and warnings.
3. `report --format markdown` returns producer-readable summary text.
4. Full uv test suite and compileall pass.
