from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "timeline.v1"
VALID_STATES = {"proposed", "accepted", "rejected"}
VALID_RISKS = {"deterministic", "low", "medium", "high"}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "media_manifest",
    "tracks",
    "timebase",
    "operations",
    "provenance",
    "export_metadata",
    "recovery",
}


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def new_operation_id(prefix: str = "op") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def create_noop_timeline(media_manifest: dict[str, Any], tracks: list[dict[str, Any]]) -> dict[str, Any]:
    audio_track = next((t for t in tracks if t.get("type") == "audio"), {})
    video_track = next((t for t in tracks if t.get("type") == "video"), None)
    sample_rate = int(audio_track.get("sample_rate") or 48000)
    timebase: dict[str, Any] = {
        "primary_time_unit": "seconds",
        "audio_sample_rate": sample_rate,
        "pts_origin": 0,
    }
    if video_track:
        timebase["video_stream_timebase"] = video_track.get("timebase", "1/90000")
        timebase["video_start_pts"] = video_track.get("start_pts", 0)
    return {
        "schema_version": SCHEMA_VERSION,
        "media_manifest": media_manifest,
        "tracks": tracks,
        "timebase": timebase,
        "operations": [],
        "provenance": {"created_by": "podcast-auto-editor", "contract": SCHEMA_VERSION},
        "export_metadata": {},
        "recovery": {"source_to_output": [], "removed_segments": [], "undo": []},
    }


def validate_timeline(timeline: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_TOP_LEVEL.difference(timeline)
    if missing:
        errors.append(f"missing top-level fields: {sorted(missing)}")
    if timeline.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(timeline.get("tracks"), list):
        errors.append("tracks must be a list")
    if not isinstance(timeline.get("operations"), list):
        errors.append("operations must be a list")
        return errors
    seen_ids: set[str] = set()
    for idx, op in enumerate(timeline.get("operations", [])):
        for key in ("operation_id", "type", "source_range", "output_range", "affected_tracks", "state", "risk", "confidence", "provenance", "preview_ref", "diff_ref", "recovery_ref"):
            if key not in op:
                errors.append(f"operation[{idx}] missing {key}")
        operation_id = op.get("operation_id")
        if operation_id in seen_ids:
            errors.append(f"operation[{idx}] duplicate operation_id {operation_id!r}")
        seen_ids.add(operation_id)
        if op.get("state") not in VALID_STATES:
            errors.append(f"operation[{idx}] invalid state {op.get('state')!r}")
        if op.get("risk") not in VALID_RISKS:
            errors.append(f"operation[{idx}] invalid risk {op.get('risk')!r}")
        source_range = op.get("source_range", {})
        if source_range.get("end", 0) <= source_range.get("start", 0):
            errors.append(f"operation[{idx}] source_range end must be after start")
        if op.get("state") == "accepted":
            for ref in ("preview_ref", "diff_ref", "recovery_ref"):
                if not op.get(ref):
                    errors.append(f"operation[{idx}] accepted operation missing {ref}")
    return errors


def seconds_to_samples(seconds: float, sample_rate: int) -> int:
    return round(seconds * sample_rate)


def samples_to_seconds(samples: int, sample_rate: int) -> float:
    return samples / sample_rate


def seconds_to_pts(seconds: float, timebase: str, start_pts: int = 0) -> int:
    numerator, denominator = (int(part) for part in timebase.split("/", 1))
    return start_pts + round(seconds * denominator / numerator)


def pts_to_seconds(pts: int, timebase: str, start_pts: int = 0) -> float:
    numerator, denominator = (int(part) for part in timebase.split("/", 1))
    return (pts - start_pts) * numerator / denominator


def accepted_cut_ranges(timeline: dict[str, Any]) -> list[dict[str, float]]:
    ranges = []
    for op in timeline.get("operations", []):
        if op.get("state") == "accepted" and op.get("type") in {"silence_cut", "retake_cut", "video_cut"}:
            source_range = op["source_range"]
            ranges.append({"start": float(source_range["start"]), "end": float(source_range["end"]), "operation_id": op["operation_id"]})
    return sorted(ranges, key=lambda item: (item["start"], item["end"]))


def kept_segments(duration: float, cuts: Iterable[dict[str, float]]) -> list[dict[str, float]]:
    kept: list[dict[str, float]] = []
    cursor = 0.0
    for cut in sorted(cuts, key=lambda item: (item["start"], item["end"])):
        start = max(0.0, min(float(cut["start"]), duration))
        end = max(0.0, min(float(cut["end"]), duration))
        if start > cursor:
            kept.append({"source_start": cursor, "source_end": start})
        cursor = max(cursor, end)
    if cursor < duration:
        kept.append({"source_start": cursor, "source_end": duration})
    out_cursor = 0.0
    for segment in kept:
        length = segment["source_end"] - segment["source_start"]
        segment["output_start"] = out_cursor
        segment["output_end"] = out_cursor + length
        out_cursor += length
    return kept


def build_recovery(timeline: dict[str, Any]) -> dict[str, Any]:
    duration = float(timeline.get("media_manifest", {}).get("duration", 0.0))
    cuts = accepted_cut_ranges(timeline)
    removed = [
        {
            "operation_id": cut["operation_id"],
            "source_start": cut["start"],
            "source_end": cut["end"],
            "duration": max(0.0, cut["end"] - cut["start"]),
        }
        for cut in cuts
    ]
    return {
        "source_to_output": kept_segments(duration, cuts),
        "removed_segments": removed,
        "undo": [{"operation_id": item["operation_id"], "action": "set_state", "state": "proposed"} for item in removed],
    }


def set_operation_state(timeline: dict[str, Any], operation_ids: Iterable[str] | None, state: str) -> dict[str, Any]:
    if state not in VALID_STATES:
        raise ValueError(f"invalid state: {state}")
    ids = set(operation_ids or [])
    updated = deepcopy(timeline)
    for op in updated.get("operations", []):
        if not ids or op.get("operation_id") in ids:
            op["state"] = state
    updated["recovery"] = build_recovery(updated)
    return updated


def write_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())
