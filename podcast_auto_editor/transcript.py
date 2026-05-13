from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


class TranscriptValidationError(ValueError):
    """Raised when an imported transcript JSON file is not safe to use."""


def _coerce_seconds(value: Any, field: str, idx: int) -> float:
    if isinstance(value, bool) or value is None:
        raise TranscriptValidationError(f"segment[{idx}].{field} must be a number")
    try:
        seconds = float(value)
    except (TypeError, ValueError) as exc:
        raise TranscriptValidationError(f"segment[{idx}].{field} must be a number") from exc
    if not math.isfinite(seconds):
        raise TranscriptValidationError(f"segment[{idx}].{field} must be finite")
    return round(seconds, 6)


def _extract_segments(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        schema_version = data.get("schema_version")
        if schema_version not in (None, "transcript.v1"):
            raise TranscriptValidationError("unsupported transcript schema_version; expected transcript.v1")
        segments = data.get("segments")
        if isinstance(segments, list):
            return segments
        raise TranscriptValidationError("transcript object must contain a segments array")
    raise TranscriptValidationError("transcript JSON must be an array or an object with segments")


def normalize_transcript_segments(data: Any) -> list[dict[str, Any]]:
    """Validate and normalize imported transcript JSON into ordered cue dicts.

    Accepted inputs are either a raw list of segment objects or an object with a
    top-level ``segments`` array. Each segment must have finite numeric
    ``start``/``end`` seconds and non-empty string ``text``. Extra fields are
    preserved so speaker/provenance metadata can flow through derived assets.
    """
    raw_segments = _extract_segments(data)
    normalized: list[dict[str, Any]] = []
    previous_start = -math.inf
    previous_end = 0.0
    for idx, raw in enumerate(raw_segments):
        if not isinstance(raw, dict):
            raise TranscriptValidationError(f"segment[{idx}] must be an object")
        missing = {field for field in ("start", "end", "text") if field not in raw}
        if missing:
            raise TranscriptValidationError(f"segment[{idx}] missing required field(s): {', '.join(sorted(missing))}")
        start = _coerce_seconds(raw["start"], "start", idx)
        end = _coerce_seconds(raw["end"], "end", idx)
        if start < 0:
            raise TranscriptValidationError(f"segment[{idx}].start must be >= 0")
        if end <= start:
            raise TranscriptValidationError(f"segment[{idx}].end must be after start")
        if start < previous_start:
            raise TranscriptValidationError(f"segment[{idx}].start must be monotonic")
        if start < previous_end:
            raise TranscriptValidationError(f"segment[{idx}] overlaps previous segment")
        text = raw["text"]
        if not isinstance(text, str):
            raise TranscriptValidationError(f"segment[{idx}].text must be a string")
        if not text.strip():
            raise TranscriptValidationError(f"segment[{idx}].text must not be empty")
        segment = dict(raw)
        segment["start"] = start
        segment["end"] = end
        segment["text"] = text
        normalized.append(segment)
        previous_start = start
        previous_end = end
    return normalized


def load_transcript_segments(path: str | Path) -> list[dict[str, Any]]:
    """Load, parse, and validate transcript segments from a JSON file."""
    path = Path(path)
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TranscriptValidationError(f"invalid transcript JSON: {exc.msg} at line {exc.lineno} column {exc.colno}") from exc
    return normalize_transcript_segments(data)
