#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
: "${UV_CACHE_DIR:=/tmp/uv-cache-podcast-auto-editor}"
export UV_CACHE_DIR
uv run --group dev pytest -q -p no:cacheprovider
uv run python -m compileall -q podcast_auto_editor tests
uv run python -m podcast_auto_editor --help >/dev/null
if command -v ffmpeg >/dev/null 2>&1; then
  uv run python -m podcast_auto_editor demo-fixtures --out /tmp/podcast-auto-editor-demo-fixtures >/dev/null
else
  echo "ffmpeg not found; skipping demo fixture generation"
fi
