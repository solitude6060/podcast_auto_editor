## Summary
- 

## Verification
- [ ] `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider`
- [ ] `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests`
- [ ] `./scripts/smoke.sh` when touching CLI, packaging, or media fixtures

## Local-only safety
- [ ] `.omx/` remains ignored and untracked (`git ls-files .omx` is empty)
- [ ] No `Co-authored-by` trailers were added unless explicitly requested
- [ ] No secrets, cloud credentials, or generated run artifacts are included
