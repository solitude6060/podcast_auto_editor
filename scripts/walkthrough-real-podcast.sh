#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/walkthrough-real-podcast.sh --audio <path> [--out <dir>] [--episode-id <id>]

Runs the PR-A2 real-podcast walkthrough with offline/mock defaults.
USAGE
}

AUDIO=""
OUT="runs/walkthrough"
EPISODE_ID="ep1-real"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --audio)
      AUDIO="${2:-}"
      shift 2
      ;;
    --out)
      OUT="${2:-}"
      shift 2
      ;;
    --episode-id)
      EPISODE_ID="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$AUDIO" ]]; then
  echo "--audio is required" >&2
  usage >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${UV_CACHE_DIR:=/tmp/uv-cache-podcast-auto-editor}"
export UV_CACHE_DIR

rm -rf "$OUT"

uv run python -m podcast_auto_editor quickstart \
  --real-audio "$AUDIO" \
  --out "$OUT" \
  --episode-id "$EPISODE_ID"

RUN_DIR="$OUT/runs/$EPISODE_ID"

cat <<NEXT

Artefacts:
  review-session.json: $RUN_DIR/review-session.json
  recipe.v1.json:      $RUN_DIR/recipe.v1.json
  ai-draft.v1.json:    $RUN_DIR/ai/ai-draft.v1.json

next: open dashboard with:
  uv run python -m podcast_auto_editor review serve $RUN_DIR
NEXT
