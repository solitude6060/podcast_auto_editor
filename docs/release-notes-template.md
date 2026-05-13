# Release notes template

Traditional Chinese version: [`release-notes-template.zh-TW.md`](release-notes-template.zh-TW.md)

## Version
`vX.Y.Z` — YYYY-MM-DD

## Highlights
- 

## User-facing changes
- 

## Compatibility notes
- Timeline schema:
- Config schema:
- CLI compatibility:

## Verification
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider`
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests`
- Optional FFmpeg acceptance smoke, when media tooling is available:

## Release checklist
- [ ] `CHANGELOG.md` updated
- [ ] Version/tag chosen
- [ ] `.omx/` and generated run artifacts are not tracked
- [ ] No secrets or cloud credentials included
- [ ] Known limitations documented
