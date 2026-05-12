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


def write_diff_artifacts(paths: RunPaths, proposed: dict[str, Any], accepted: dict[str, Any]) -> None:
    ensure_run_dirs(paths)
    proposed_ops = {op["operation_id"]: op for op in proposed.get("operations", [])}
    accepted_ops = {op["operation_id"]: op for op in accepted.get("operations", [])}
    diff = {
        "proposed_count": len(proposed_ops),
        "accepted_count": sum(1 for op in accepted_ops.values() if op.get("state") == "accepted"),
        "rejected_count": sum(1 for op in accepted_ops.values() if op.get("state") == "rejected"),
        "operations": list(accepted_ops.values()),
    }
    removed = accepted.get("recovery", {}).get("removed_segments", [])
    write_json(paths.timeline_diff, diff)
    write_json(paths.removed_segments, removed)
    lines = ["# Podcast Auto Editor Diff", "", f"Accepted edits: {diff['accepted_count']}", f"Removed segments: {len(removed)}", ""]
    for item in removed:
        lines.append(f"- {item['operation_id']}: {item['source_start']:.3f}s–{item['source_end']:.3f}s")
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
