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

if [[ -z "$OUT" ]]; then
  echo "unsafe path for --out: empty path" >&2
  exit 2
fi

if [[ "$AUDIO" != /* ]]; then
  AUDIO="$(realpath -m "$AUDIO")"
fi
if [[ "$OUT" != /* ]]; then
  OUT="$(realpath -m "$OUT")"
fi

HOME_REAL="$(realpath -m "$HOME")"
ROOT_REAL="$(realpath -m "$ROOT")"
OUT_REAL="$(realpath -m "$OUT")"

path_is_self_or_ancestor() {
  local candidate="$1"
  local target="$2"
  [[ "$candidate" == "$target" || "$target" == "$candidate"/* ]]
}

if [[ "$OUT_REAL" == "/" ]] || path_is_self_or_ancestor "$OUT_REAL" "$HOME_REAL" || path_is_self_or_ancestor "$OUT_REAL" "$ROOT_REAL"; then
  echo "unsafe path for --out: $OUT" >&2
  exit 2
fi

cd "$ROOT"

: "${UV_CACHE_DIR:=/tmp/uv-cache-podcast-auto-editor}"
export UV_CACHE_DIR

rm -rf "$OUT_REAL"

uv run python -m podcast_auto_editor quickstart \
  --real-audio "$AUDIO" \
  --out "$OUT_REAL" \
  --episode-id "$EPISODE_ID"

RUN_DIR="$OUT_REAL/runs/$EPISODE_ID"

cat <<NEXT

Artefacts:
  review-session.json: $RUN_DIR/review-session.json
  recipe.v1.json:      $RUN_DIR/recipe.v1.json
  ai-draft.v1.json:    $RUN_DIR/ai/ai-draft.v1.json

next: open dashboard with:
  uv run python -m podcast_auto_editor review serve $RUN_DIR
NEXT
