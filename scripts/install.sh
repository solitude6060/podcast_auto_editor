#!/usr/bin/env bash
# Podcast Auto Editor — local installer (Linux + uv path)
#
# Idempotent: run twice and the second invocation is a no-op aside from
# refreshing the uv sync. macOS / WSL is documented but not verified by
# this script; see README for those platforms.
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed; install it first: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${UV_CACHE_DIR:=/tmp/uv-cache-podcast-auto-editor}"
export UV_CACHE_DIR

echo "Syncing dev dependencies via uv..."
uv sync --group dev

if command -v ffmpeg >/dev/null 2>&1; then
  echo "Generating demo fixtures (ffmpeg available)..."
  uv run python -m podcast_auto_editor demo-fixtures --out demo-fixtures >/dev/null
else
  echo "ffmpeg not found; skipping demo fixture generation. Install ffmpeg to use the full demo." >&2
fi

cat <<'NEXT'

Install ok. Next steps:

  uv run python -m podcast_auto_editor quickstart
  uv run python -m podcast_auto_editor review serve <run-dir>

Run `uv run python -m podcast_auto_editor --help` to see the full CLI.
NEXT
