from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .timeline import write_json

_EPISODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


@dataclass(frozen=True)
class RunPaths:
    root: Path
    manifest: Path
    raw_probe: Path
    proposed_timeline: Path
    accepted_timeline: Path
    timeline_diff: Path
    removed_segments: Path
    human_summary: Path
    before_after_preview: Path
    removed_segments_preview: Path
    waveform: Path
    recovery_map: Path
    undo_accepted_ops: Path
    restore_instructions: Path
    exports: Path
    edited_wav: Path
    edited_mp3: Path
    edited_mp4: Path
    transcript: Path
    subtitles_srt: Path
    subtitles_vtt: Path
    chapters: Path


def validate_episode_id(episode_id: str) -> None:
    if not episode_id or not _EPISODE_RE.match(episode_id):
        raise ValueError("episode_id must contain only letters, numbers, underscore, dash, or dot and may not be empty")
    if ".." in episode_id or episode_id.startswith(('/', '~')):
        raise ValueError("episode_id may not traverse paths")


def run_paths(base_dir: str | Path, episode_id: str) -> RunPaths:
    validate_episode_id(episode_id)
    root = Path(base_dir) / episode_id
    return RunPaths(
        root=root,
        manifest=root / "manifest.json",
        raw_probe=root / "raw_probe.json",
        proposed_timeline=root / "timeline.proposed.v1.json",
        accepted_timeline=root / "timeline.accepted.v1.json",
        timeline_diff=root / "diff" / "timeline-diff.json",
        removed_segments=root / "diff" / "removed-segments.json",
        human_summary=root / "diff" / "human-summary.md",
        before_after_preview=root / "preview" / "before-after-preview.mp3",
        removed_segments_preview=root / "preview" / "removed-segments-preview.mp3",
        waveform=root / "preview" / "waveform.json",
        recovery_map=root / "recovery" / "recovery-map.json",
        undo_accepted_ops=root / "recovery" / "undo-accepted-ops.json",
        restore_instructions=root / "recovery" / "restore-instructions.md",
        exports=root / "exports",
        edited_wav=root / "exports" / "episode.edited.wav",
        edited_mp3=root / "exports" / "episode.edited.mp3",
        edited_mp4=root / "exports" / "episode.edited.mp4",
        transcript=root / "exports" / "transcript.json",
        subtitles_srt=root / "exports" / "subtitles.srt",
        subtitles_vtt=root / "exports" / "subtitles.vtt",
        chapters=root / "exports" / "chapters.json",
    )


def ensure_run_dirs(paths: RunPaths) -> None:
    for directory in (paths.root, paths.timeline_diff.parent, paths.before_after_preview.parent, paths.recovery_map.parent, paths.exports):
        directory.mkdir(parents=True, exist_ok=True)


def _format_seconds(value: float) -> str:
    return f"{value:.3f}s"


def _operation_reason(operation: dict[str, Any]) -> str:
    provenance = operation.get("provenance", {})
    manual_review = provenance.get("manual_review")
    if isinstance(manual_review, dict) and manual_review.get("note"):
        return str(manual_review["note"])
    auto_accept_policy = provenance.get("auto_accept_policy")
    if auto_accept_policy:
        return str(auto_accept_policy)
    silence = provenance.get("silence")
    if isinstance(silence, dict) and silence.get("threshold_db"):
        return f"silence below {silence['threshold_db']} dB"
    return ""


def _markdown_table_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _removed_segment_metadata(removed: list[dict[str, Any]], operations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for item in removed:
        operation = operations.get(item.get("operation_id", ""), {})
        enriched.append(
            {
                **item,
                "operation_type": operation.get("type", "unknown"),
                "risk": operation.get("risk", "unknown"),
                "confidence": operation.get("confidence"),
                "reason": _operation_reason(operation),
                "preview_ref": operation.get("preview_ref"),
                "diff_ref": operation.get("diff_ref"),
                "recovery_ref": operation.get("recovery_ref"),
            }
        )
    return enriched


def write_diff_artifacts(paths: RunPaths, proposed: dict[str, Any], accepted: dict[str, Any]) -> None:
    ensure_run_dirs(paths)
    proposed_ops = {op["operation_id"]: op for op in proposed.get("operations", [])}
    accepted_ops = {op["operation_id"]: op for op in accepted.get("operations", [])}
    removed = accepted.get("recovery", {}).get("removed_segments", [])
    removed_metadata = _removed_segment_metadata(removed, accepted_ops)
    total_removed_duration = sum(float(item.get("duration", 0.0)) for item in removed)
    diff = {
        "proposed_count": len(proposed_ops),
        "accepted_count": sum(1 for op in accepted_ops.values() if op.get("state") == "accepted"),
        "rejected_count": sum(1 for op in accepted_ops.values() if op.get("state") == "rejected"),
        "proposed_only_count": len(set(proposed_ops).difference(accepted_ops)),
        "total_removed_duration": total_removed_duration,
        "operations": list(accepted_ops.values()),
        "removed_segments": removed_metadata,
    }
    write_json(paths.timeline_diff, diff)
    write_json(paths.removed_segments, removed_metadata)
    lines = [
        "# Podcast Auto Editor Diff",
        "",
        "## Summary",
        "",
        f"- Proposed edits: {diff['proposed_count']}",
        f"- Accepted edits: {diff['accepted_count']}",
        f"- Rejected edits: {diff['rejected_count']}",
        f"- Removed segments: {len(removed_metadata)}",
        f"- Total removed duration: {_format_seconds(total_removed_duration)}",
        "",
        "## Removed Segments",
        "",
    ]
    if removed_metadata:
        lines.extend(
            [
                "| Operation | Type | Source range | Duration | Risk | Confidence | Preview | Reason |",
                "| --- | --- | --- | ---: | --- | ---: | --- | --- |",
            ]
        )
        for item in removed_metadata:
            confidence = "" if item.get("confidence") is None else f"{float(item['confidence']):.2f}"
            source_range = f"{_format_seconds(float(item['source_start']))}–{_format_seconds(float(item['source_end']))}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_table_cell(item["operation_id"]),
                        _markdown_table_cell(item["operation_type"]),
                        source_range,
                        _format_seconds(float(item["duration"])),
                        _markdown_table_cell(item["risk"]),
                        confidence,
                        _markdown_table_cell(item.get("preview_ref") or ""),
                        _markdown_table_cell(item.get("reason") or ""),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No accepted edits remove source audio.")
    paths.human_summary.write_text("\n".join(lines) + "\n")


def write_recovery_artifacts(paths: RunPaths, timeline: dict[str, Any]) -> None:
    ensure_run_dirs(paths)
    recovery = timeline.get("recovery", {})
    write_json(paths.recovery_map, recovery.get("source_to_output", []))
    write_json(paths.undo_accepted_ops, recovery.get("undo", []))
    paths.restore_instructions.write_text(
        "# Restore Instructions\n\n"
        "Use recovery-map.json to map edited output ranges back to original source ranges. "
        "Set accepted operation states back to proposed/rejected and re-render to undo edits.\n"
    )


def write_manifest(paths: RunPaths, payload: dict[str, Any]) -> None:
    ensure_run_dirs(paths)
    write_json(paths.manifest, payload)
