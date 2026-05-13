from __future__ import annotations

import json
import shutil
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .artifacts import RunPaths, ensure_run_dirs, run_paths, write_diff_artifacts, write_manifest, write_recovery_artifacts
from .config import AppConfig, config_to_dict
from .media import MediaToolError, detect_silence, measure_audio_quality, measure_av_sync, probe_media, render_audio, render_video
from .quality import evaluate_quality
from .retake import detect_retake_candidates, may_auto_accept_retake
from .silence import propose_silence_cuts
from .subtitles import cues_to_srt, cues_to_vtt, heuristic_chapters, validate_chapters, validate_cues
from .timeline import accepted_cut_ranges, build_recovery, create_noop_timeline, kept_segments, read_json, set_operation_state, validate_timeline, write_json


def episode_id_from_path(path: str | Path) -> str:
    stem = Path(path).stem or "episode"
    return "".join(ch if ch.isalnum() or ch in "_.-" else "-" for ch in stem).strip(".-_") or "episode"


def probe(input_path: str | Path, paths: RunPaths, config: AppConfig) -> dict[str, Any]:
    manifest, tracks = probe_media(input_path)
    timeline = create_noop_timeline(manifest, tracks)
    timeline["export_metadata"]["config"] = config_to_dict(config)
    ensure_run_dirs(paths)
    write_json(paths.raw_probe, {"media_manifest": manifest, "tracks": tracks})
    write_json(paths.proposed_timeline, timeline)
    write_manifest(paths, {"input": str(input_path), "episode_id": paths.root.name, "config": config_to_dict(config)})
    errors = validate_timeline(timeline)
    if errors:
        raise ValueError("invalid no-op timeline: " + "; ".join(errors))
    return timeline


def analyze(input_path: str | Path, timeline: dict[str, Any], config: AppConfig) -> dict[str, Any]:
    try:
        segments = detect_silence(input_path, config)
    except MediaToolError:
        segments = []
    proposed = dict(timeline)
    proposed["operations"] = list(timeline.get("operations", [])) + propose_silence_cuts(segments, config.quality)
    proposed["export_metadata"] = dict(proposed.get("export_metadata", {}), silence_segments=segments, config=config_to_dict(config))
    return proposed


def add_retake_proposals(timeline: dict[str, Any], transcript_segments: list[dict[str, Any]], config: AppConfig, artifacts_exist: bool = False) -> dict[str, Any]:
    updated = dict(timeline)
    ops = list(timeline.get("operations", []))
    for op in detect_retake_candidates(transcript_segments, config.retake):
        may_accept, reason = may_auto_accept_retake(op, config.retake, artifacts_exist=artifacts_exist)
        op["provenance"]["auto_accept_policy"] = reason
        if may_accept:
            op["state"] = "accepted"
        ops.append(op)
    updated["operations"] = ops
    updated["recovery"] = build_recovery(updated)
    return updated


def _attach_artifact_refs(op: dict[str, Any]) -> None:
    op["preview_ref"] = op.get("preview_ref") or "preview/before-after-preview.mp3"
    op["diff_ref"] = op.get("diff_ref") or "diff/timeline-diff.json"
    op["recovery_ref"] = op.get("recovery_ref") or "recovery/recovery-map.json"


def accept_safe_defaults(timeline: dict[str, Any]) -> dict[str, Any]:
    """Accept deterministic cuts only; speech/retake edits stay proposed by default."""
    accepted = dict(timeline)
    accepted["operations"] = [dict(op) for op in timeline.get("operations", [])]
    for op in accepted["operations"]:
        if op.get("risk") == "deterministic" and op.get("type") == "silence_cut":
            op["state"] = "accepted"
            _attach_artifact_refs(op)
        elif op.get("type") == "retake_cut":
            op["state"] = "proposed"
    accepted["recovery"] = build_recovery(accepted)
    return accepted


def apply_retake_auto_accept_policy(timeline: dict[str, Any], config: AppConfig) -> dict[str, Any]:
    updated = dict(timeline)
    updated["operations"] = [dict(op) for op in timeline.get("operations", [])]
    for op in updated["operations"]:
        if op.get("type") != "retake_cut":
            continue
        _attach_artifact_refs(op)
        may_accept, reason = may_auto_accept_retake(op, config.retake, artifacts_exist=True)
        op.setdefault("provenance", {})["auto_accept_policy"] = reason
        if may_accept:
            op["state"] = "accepted"
    updated["recovery"] = build_recovery(updated)
    return updated


def accept_all(timeline: dict[str, Any]) -> dict[str, Any]:
    """Explicit user acceptance path: accept all operations and attach required refs."""
    accepted = set_operation_state(timeline, None, "accepted")
    for op in accepted.get("operations", []):
        _attach_artifact_refs(op)
    accepted["recovery"] = build_recovery(accepted)
    return accepted


def review_accept_operations(
    timeline: dict[str, Any],
    operation_ids: list[str],
    reviewer: str,
    note: str = "",
    reviewed_at: str | None = None,
) -> dict[str, Any]:
    """Accept selected retake operations after explicit human review.

    This is intentionally not a bulk-accept helper: retake cuts affect speech
    meaning, so every accepted retake must be named by operation id and carry
    review provenance before render is allowed.
    """
    if not operation_ids:
        raise ValueError("review acceptance requires at least one operation id")
    reviewer = reviewer.strip()
    if not reviewer:
        raise ValueError("reviewer may not be empty")
    selected = set(operation_ids)
    updated = deepcopy(timeline)
    seen: set[str] = set()
    reviewed_at = reviewed_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for op in updated.get("operations", []):
        operation_id = op.get("operation_id")
        if operation_id not in selected:
            continue
        seen.add(operation_id)
        if op.get("type") != "retake_cut":
            raise ValueError(f"operation {operation_id} is not a retake_cut")
        op["state"] = "accepted"
        _attach_artifact_refs(op)
        op.setdefault("provenance", {})["manual_review"] = {
            "decision": "accepted",
            "reviewer": reviewer,
            "note": note,
            "reviewed_at": reviewed_at,
        }
    missing = selected.difference(seen)
    if missing:
        raise ValueError(f"unknown operation id(s): {', '.join(sorted(missing))}")
    updated["recovery"] = build_recovery(updated)
    return updated


def retake_operation_is_render_safe(operation: dict[str, Any]) -> bool:
    if operation.get("type") != "retake_cut":
        return True
    provenance = operation.get("provenance", {})
    auto_policy = str(provenance.get("auto_accept_policy", ""))
    if auto_policy.startswith("accepted"):
        return True
    manual_review = provenance.get("manual_review", {})
    return (
        manual_review.get("decision") == "accepted"
        and bool(str(manual_review.get("reviewer", "")).strip())
        and bool(str(manual_review.get("reviewed_at", "")).strip())
    )


def undo_accepted_operations(
    timeline: dict[str, Any],
    operation_ids: list[str] | None,
    undo_all: bool = False,
    reason: str = "",
    undone_at: str | None = None,
) -> dict[str, Any]:
    """Restore accepted operations back to proposed and rebuild recovery."""
    ids = set(operation_ids or [])
    if undo_all and ids:
        raise ValueError("undo accepts either --all or --operation-id, not both")
    if not undo_all and not ids:
        raise ValueError("undo requires --all or at least one --operation-id")
    updated = deepcopy(timeline)
    operations = updated.get("operations", [])
    known_ids = {op.get("operation_id") for op in operations}
    missing = ids.difference(known_ids)
    if missing:
        raise ValueError(f"unknown operation id(s): {', '.join(sorted(missing))}")
    targets = [op for op in operations if (undo_all and op.get("state") == "accepted") or op.get("operation_id") in ids]
    for op in targets:
        operation_id = op.get("operation_id")
        if op.get("state") != "accepted":
            raise ValueError(f"operation {operation_id} is not accepted")
    undone_at = undone_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for op in targets:
        op["state"] = "proposed"
        op.setdefault("provenance", {})["undo"] = {
            "previous_state": "accepted",
            "restored_state": "proposed",
            "reason": reason,
            "undone_at": undone_at,
        }
    updated["recovery"] = build_recovery(updated)
    return updated


def _preview_segment_metadata(timeline: dict[str, Any]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for op in timeline.get("operations", []):
        source_range = op.get("source_range") or {}
        if "start" not in source_range or "end" not in source_range:
            continue
        start = float(source_range["start"])
        end = float(source_range["end"])
        segments.append(
            {
                "operation_id": op.get("operation_id"),
                "operation_type": op.get("type"),
                "state": op.get("state"),
                "source_start": start,
                "source_end": end,
                "duration": max(0.0, end - start),
                "risk": op.get("risk"),
                "confidence": op.get("confidence"),
            }
        )
    return segments


def write_preview(paths: RunPaths, input_path: str | Path, timeline: dict[str, Any]) -> None:
    ensure_run_dirs(paths)
    preview_segments = _preview_segment_metadata(timeline)
    paths.waveform.write_text(
        json.dumps(
            {
                "type": "timeline-preview",
                "operations": timeline.get("operations", []),
                "removed_segments_preview": {
                    "path": str(paths.removed_segments_preview),
                    "segment_count": len(preview_segments),
                    "total_duration": sum(segment["duration"] for segment in preview_segments),
                    "segments": preview_segments,
                },
            },
            indent=2,
        )
        + "\n"
    )
    if not Path(input_path).exists():
        raise MediaToolError(f"input media does not exist: {input_path}")
    # Real preview artifact: short transcoded preview of the source media.
    from .media import require_tool, run_command
    require_tool("ffmpeg")
    result = run_command(["ffmpeg", "-y", "-hide_banner", "-t", "30", "-i", str(input_path), "-vn", "-acodec", "libmp3lame", str(paths.before_after_preview)])
    if result.returncode != 0:
        raise MediaToolError(result.stderr.strip() or "preview generation failed")
    if preview_segments:
        select_expr = "+".join(f"between(t,{segment['source_start']:.6f},{segment['source_end']:.6f})" for segment in preview_segments)
        result = run_command([
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-i",
            str(input_path),
            "-af",
            f"aselect='{select_expr}',asetpts=N/SR/TB",
            "-vn",
            "-acodec",
            "libmp3lame",
            str(paths.removed_segments_preview),
        ])
    else:
        result = run_command(["ffmpeg", "-y", "-hide_banner", "-t", "30", "-i", str(input_path), "-vn", "-acodec", "libmp3lame", str(paths.removed_segments_preview)])
    if result.returncode != 0:
        raise MediaToolError(result.stderr.strip() or "removed-segments preview generation failed")


def render(input_path: str | Path, paths: RunPaths, timeline: dict[str, Any], config: AppConfig) -> dict[str, Any]:
    duration = float(timeline.get("media_manifest", {}).get("duration", 0.0))
    kept = kept_segments(duration, accepted_cut_ranges(timeline))
    channels = 2
    for track in timeline.get("tracks", []):
        if track.get("type") == "audio":
            channels = int(track.get("channels", channels))
            break
    render_audio(input_path, paths.edited_wav, kept, config, channels=channels)
    metrics = measure_audio_quality(paths.edited_wav)
    av_sync_report = None
    if any(track.get("type") == "video" for track in timeline.get("tracks", [])):
        render_video(input_path, paths.edited_mp4, kept)
        av_sync_report = measure_av_sync(paths.edited_mp4)
    gate_report = evaluate_quality(metrics, channels, config.quality)
    if av_sync_report is not None:
        gate_report["checks"].append({"name": "av_sync", "passed": av_sync_report["passed"], "target": av_sync_report["tolerance_s"], "actual": av_sync_report["drift_s"]})
        gate_report["passed"] = gate_report["passed"] and av_sync_report["passed"]
    timeline.setdefault("export_metadata", {})["quality_gate_report"] = gate_report
    timeline["export_metadata"]["edited_audio"] = str(paths.edited_wav)
    if paths.edited_mp4.exists():
        timeline["export_metadata"]["edited_video"] = str(paths.edited_mp4)
    if not gate_report["passed"]:
        failed = ", ".join(check["name"] for check in gate_report["checks"] if not check["passed"])
        raise MediaToolError(f"quality gate failed: {failed}")
    return timeline


def _clean_seconds(value: float) -> float:
    rounded = round(value, 6)
    return 0.0 if rounded == -0.0 else rounded


def remap_cues_to_output(cues: list[dict[str, Any]], recovery: dict[str, Any]) -> list[dict[str, Any]]:
    """Map source-timestamp transcript cues onto the edited output timeline."""
    kept_segments = recovery.get("source_to_output", [])
    if not kept_segments:
        return [dict(cue) for cue in cues]
    remapped: list[dict[str, Any]] = []
    for cue in cues:
        cue_start = float(cue.get("start", 0.0))
        cue_end = float(cue.get("end", cue_start))
        if cue_end <= cue_start:
            continue
        for kept in kept_segments:
            source_start = float(kept["source_start"])
            source_end = float(kept["source_end"])
            overlap_start = max(cue_start, source_start)
            overlap_end = min(cue_end, source_end)
            if overlap_end <= overlap_start:
                continue
            offset = float(kept["output_start"]) - source_start
            mapped = dict(cue)
            mapped["start"] = _clean_seconds(overlap_start + offset)
            mapped["end"] = _clean_seconds(overlap_end + offset)
            remapped.append(mapped)
    return remapped


def transcribe_and_write(paths: RunPaths, timeline: dict[str, Any], cues: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    ensure_run_dirs(paths)
    duration = float(timeline.get("recovery", {}).get("source_to_output", [{}])[-1].get("output_end", timeline.get("media_manifest", {}).get("duration", 0.0))) if timeline.get("recovery", {}).get("source_to_output") else float(timeline.get("media_manifest", {}).get("duration", 0.0))
    cues = remap_cues_to_output(cues if cues is not None else [], timeline.get("recovery", {}))
    transcript = {
        "source": "post-edit-stub",
        "final_render": str(paths.edited_wav),
        "accepted_timeline": str(paths.accepted_timeline),
        "duration": duration,
        "segments": cues,
    }
    chapters = heuristic_chapters(cues, duration)
    cue_errors = validate_cues(cues, duration)
    chapter_errors = validate_chapters(chapters, duration)
    write_json(paths.transcript, transcript)
    paths.subtitles_srt.write_text(cues_to_srt(cues))
    paths.subtitles_vtt.write_text(cues_to_vtt(cues))
    write_json(paths.chapters, chapters)
    timeline.setdefault("export_metadata", {})["derived_assets"] = {
        "transcript": str(paths.transcript),
        "subtitles_srt": str(paths.subtitles_srt),
        "subtitles_vtt": str(paths.subtitles_vtt),
        "chapters": str(paths.chapters),
        "cue_errors": cue_errors,
        "chapter_errors": chapter_errors,
    }
    return timeline


def run_pipeline(input_path: str | Path, output_dir: str | Path, config: AppConfig, episode_id: str | None = None, transcript_segments: list[dict[str, Any]] | None = None) -> RunPaths:
    episode_id = episode_id or episode_id_from_path(input_path)
    paths = run_paths(output_dir, episode_id)
    timeline = probe(input_path, paths, config)
    proposed = analyze(input_path, timeline, config)
    if transcript_segments:
        proposed = add_retake_proposals(proposed, transcript_segments, config, artifacts_exist=False)
    write_json(paths.proposed_timeline, proposed)
    write_preview(paths, input_path, proposed)
    accepted = accept_safe_defaults(proposed)
    write_diff_artifacts(paths, proposed, accepted)
    write_recovery_artifacts(paths, accepted)
    accepted = apply_retake_auto_accept_policy(accepted, config)
    write_diff_artifacts(paths, proposed, accepted)
    write_recovery_artifacts(paths, accepted)
    accepted = render(input_path, paths, accepted, config)
    accepted = transcribe_and_write(paths, accepted, cues=transcript_segments or [])
    write_json(paths.accepted_timeline, accepted)
    write_manifest(paths, {"input": str(input_path), "episode_id": episode_id, "artifacts": {"accepted_timeline": str(paths.accepted_timeline), "transcript": str(paths.transcript)}, "config": config_to_dict(config)})
    return paths
