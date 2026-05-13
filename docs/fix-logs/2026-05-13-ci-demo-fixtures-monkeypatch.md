# CI demo-fixtures monkeypatch fix

## Failure
GitHub Actions run `25805199794` failed on `tests/test_fixtures.py::test_demo_fixtures_cli_prints_paths` because the runner did not have `ffmpeg` installed.

The test intended to avoid real media generation by monkeypatching `fixtures.make_demo_fixtures`, but `podcast_auto_editor.cli` imports `make_demo_fixtures` directly. The CLI kept calling the original function and reached `require_tool("ffmpeg")`.

## Fix
Monkeypatch `podcast_auto_editor.cli.make_demo_fixtures` in the CLI test so the test remains a pure CLI output test and does not depend on FFmpeg.

## Verification
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q tests/test_fixtures.py::test_demo_fixtures_cli_prints_paths -p no:cacheprovider`
- Full uv pytest and compileall before push.
