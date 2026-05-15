# Dev-to-Main Stage Review: whisper.cpp local ASR provider

Date: 2026-05-15
PR: https://github.com/solitude6060/podcast_auto_editor/pull/15
Branch: `dev` → `main`

## Scope

Promote the optional `whisper-cpp-local` ASR provider after feature PR #14 merged into `dev`.

## Evidence checklist

- Feature PR review exists: `docs/reviews/2026-05-15-pr14-whisper-cpp-provider.md`.
- Plan artifacts exist in English and Traditional Chinese.
- User-facing docs exist in English and Traditional Chinese.
- `.omx` remains untracked.
- No `Co-authored-by` trailers were introduced.

## Verification on `dev`

- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → `147 passed in 2.42s`.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests` → passed.
- `git diff --check` → passed.
- `git ls-files .omx` → no tracked `.omx` files.
- `git log --format='%h %s%n%b' -20 | grep -i 'Co-authored-by' || true` → no matches.

## CI

- Feature PR #14 latest CI run `25893215584` → success.
- Dev-to-main PR #15 CI run `25893251519` → success.

## Decision

Approved for merge from `dev` into `main`.
