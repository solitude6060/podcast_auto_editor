from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifacts import ensure_run_dirs, run_paths, write_diff_artifacts, write_manifest, write_recovery_artifacts
from .config import config_to_dict, load_config
from .explain import explain_operation, format_explanation_markdown
from .exports import select_export_profiles
from .fixtures import make_demo_fixtures
from .pipeline import accept_safe_defaults, add_retake_proposals, analyze, episode_id_from_path, probe, render, retake_operation_is_render_safe, review_accept_operations, run_pipeline, transcribe_and_write, undo_accepted_operations, write_preview
from .transcript import TranscriptValidationError, load_transcript_segments
from .timeline import read_json, set_operation_state, validate_timeline, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="podcast-auto-editor", description="Local-first podcast auto-editor MVP")
    parser.add_argument("--config", help="Optional JSON config path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_probe = sub.add_parser("probe")
    p_probe.add_argument("input")
    p_probe.add_argument("--out", default="runs")
    p_probe.add_argument("--episode-id")

    p_analyze = sub.add_parser("analyze")
    p_analyze.add_argument("input")
    p_analyze.add_argument("--timeline", required=True)
    p_analyze.add_argument("--out", required=True)

    p_accept = sub.add_parser("accept")
    p_accept.add_argument("timeline")
    p_accept.add_argument("--operation-id", action="append")
    p_accept.add_argument("--out", required=True)

    p_reject = sub.add_parser("reject")
    p_reject.add_argument("timeline")
    p_reject.add_argument("--operation-id", action="append")
    p_reject.add_argument("--out", required=True)

    p_review_accept = sub.add_parser("review-accept")
    p_review_accept.add_argument("timeline")
    p_review_accept.add_argument("--operation-id", action="append")
    p_review_accept.add_argument("--reviewer", required=True)
    p_review_accept.add_argument("--note", default="")
    p_review_accept.add_argument("--out", required=True)

    p_undo = sub.add_parser("undo", help="Restore accepted timeline operations back to proposed")
    p_undo.add_argument("timeline")
    p_undo.add_argument("--operation-id", action="append")
    p_undo.add_argument("--all", action="store_true", help="Undo all currently accepted operations")
    p_undo.add_argument("--reason", default="")
    p_undo.add_argument("--out", required=True)

    p_render = sub.add_parser("render")
    p_render.add_argument("input")
    p_render.add_argument("--timeline", required=True)
    p_render.add_argument("--out", default="runs")
    p_render.add_argument("--episode-id")
    p_render.add_argument("--accept-safe-defaults", action="store_true", help="Accept deterministic silence cuts only before rendering")
    p_render.add_argument("--export-profile", action="append", help="Render only the named export profile; repeat for multiple profiles")

    p_run = sub.add_parser("run")
    p_run.add_argument("input")
    p_run.add_argument("--out", default="runs")
    p_run.add_argument("--episode-id")
    p_run.add_argument("--transcript-json", help="Optional transcript JSON: either a segment array or an object with a segments array")
    p_run.add_argument("--export-profile", action="append", help="Render only the named export profile; repeat for multiple profiles")

    p_dry_run = sub.add_parser("dry-run", help="Write inspection artifacts without rendering edited media exports")
    p_dry_run.add_argument("input")
    p_dry_run.add_argument("--out", default="runs")
    p_dry_run.add_argument("--episode-id")
    p_dry_run.add_argument("--transcript-json", help="Optional transcript JSON: either a segment array or an object with a segments array")

    p_report = sub.add_parser("report", help="Summarize a run directory")
    p_report.add_argument("run_dir")
    p_report.add_argument("--format", choices=("json", "markdown"), default="markdown")

    p_review_list = sub.add_parser("review-list", help="List timeline operations with preview refs for producer review")
    p_review_list.add_argument("timeline")
    p_review_list.add_argument("--format", choices=("json", "markdown"), default="markdown")

    p_explain = sub.add_parser("explain", help="Explain one timeline operation with detector evidence and review requirements")
    p_explain.add_argument("timeline")
    p_explain.add_argument("--operation-id", required=True)
    p_explain.add_argument("--format", choices=("json", "markdown"), default="markdown")

    p_validate_transcript = sub.add_parser("validate-transcript", help="Validate transcript JSON import shape")
    p_validate_transcript.add_argument("transcript_json")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("timeline")

    p_demo = sub.add_parser("demo-fixtures", help="Generate deterministic demo media fixtures with ffmpeg when available")
    p_demo.add_argument("--out", default="demo-fixtures")
    return parser


def _load_optional_transcript(path: str | None) -> list[dict] | None:
    if not path:
        return None
    return load_transcript_segments(path)


def _build_run_report(run_dir: str | Path) -> dict:
    root = Path(run_dir)
    diff = read_json(root / "diff" / "timeline-diff.json") if (root / "diff" / "timeline-diff.json").exists() else {}
    accepted = read_json(root / "timeline.accepted.v1.json") if (root / "timeline.accepted.v1.json").exists() else {}
    derived = accepted.get("export_metadata", {}).get("derived_assets", {})
    quality = accepted.get("export_metadata", {}).get("quality_gate_report")
    warnings = []
    for key in ("cue_errors", "chapter_errors"):
        warnings.extend(derived.get(key, []) or [])
    operations = accepted.get("operations", []) if isinstance(accepted.get("operations"), list) else []
    return {
        "run_dir": str(root),
        "operation_counts": {
            "proposed": diff.get("proposed_count", 0),
            "accepted": diff.get("accepted_count", 0),
            "rejected": diff.get("rejected_count", 0),
        },
        "operation_groups": _group_operations_for_report(operations),
        "total_removed_duration": diff.get("total_removed_duration", 0.0),
        "quality_gate": quality,
        "derived_assets": {key: value for key, value in derived.items() if key not in {"cue_errors", "chapter_errors"}},
        "warnings": warnings,
    }


def _count_by(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _group_operations_for_report(operations: list[dict]) -> dict:
    return {
        "by_risk": _count_by([str(op.get("risk") or "unknown") for op in operations]),
        "by_detector": _count_by([str(op.get("provenance", {}).get("detector") or "unknown") for op in operations]),
    }


def _format_run_report_markdown(report: dict) -> str:
    counts = report["operation_counts"]
    lines = [
        "# Podcast Auto Editor Report",
        "",
        f"Run directory: {report['run_dir']}",
        "",
        "## Edits",
        "",
        f"- Proposed edits: {counts['proposed']}",
        f"- Accepted edits: {counts['accepted']}",
        f"- Rejected edits: {counts['rejected']}",
        f"- Total removed duration: {float(report['total_removed_duration']):.3f}s",
        "",
        "## Operation groups",
        "",
    ]
    groups = report.get("operation_groups") or {}
    for label, values in (("Risk", groups.get("by_risk") or {}), ("Detector", groups.get("by_detector") or {})):
        lines.append(f"### {label}")
        lines.append("")
        if values:
            lines.extend(f"- {key}: {value}" for key, value in values.items())
        else:
            lines.append("- none")
        lines.append("")
    lines.extend([
        "## Quality",
        "",
        f"- Quality gate: {report['quality_gate'].get('passed') if isinstance(report.get('quality_gate'), dict) else 'not measured'}",
        "",
        "## Warnings",
        "",
    ])
    warnings = report.get("warnings") or []
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- none")
    return "\n".join(lines) + "\n"


def _operation_preview_refs(op: dict) -> tuple[str | None, str | None]:
    operation_preview = op.get("provenance", {}).get("operation_preview", {})
    before_after_ref = operation_preview.get("before_after_ref") or op.get("preview_ref")
    removed_ref = operation_preview.get("removed_ref")
    return before_after_ref, removed_ref


def _build_review_list(timeline_path: str | Path, timeline: dict) -> dict:
    rows = []
    for op in timeline.get("operations", []):
        source = op.get("source_range") or {}
        preview_ref, removed_ref = _operation_preview_refs(op)
        rows.append({
            "operation_id": op.get("operation_id"),
            "type": op.get("type"),
            "state": op.get("state"),
            "risk": op.get("risk"),
            "confidence": op.get("confidence"),
            "source": {
                "start": float(source["start"]) if "start" in source else None,
                "end": float(source["end"]) if "end" in source else None,
            },
            "preview_ref": preview_ref,
            "removed_ref": removed_ref,
        })
    return {
        "timeline": str(timeline_path),
        "operation_count": len(rows),
        "operations": rows,
    }


def _format_source_range(source: dict) -> str:
    start = source.get("start")
    end = source.get("end")
    if start is None or end is None:
        return "-"
    return f"{float(start):.3f}-{float(end):.3f}"


def _format_confidence(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def _format_review_list_markdown(review: dict) -> str:
    lines = [
        "# Review List",
        "",
        f"Timeline: {review['timeline']}",
        f"Operations: {review['operation_count']}",
        "",
        "| Operation | Type | State | Risk | Confidence | Source | Preview | Removed |",
        "| --- | --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for op in review["operations"]:
        lines.append(
            " | ".join(
                [
                    f"| {op.get('operation_id') or '-'}",
                    str(op.get("type") or "-"),
                    str(op.get("state") or "-"),
                    str(op.get("risk") or "-"),
                    _format_confidence(op.get("confidence")),
                    _format_source_range(op.get("source") or {}),
                    str(op.get("preview_ref") or "-"),
                    f"{op.get('removed_ref') or '-'} |",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.command == "probe":
        episode_id = args.episode_id or episode_id_from_path(args.input)
        paths = run_paths(args.out, episode_id)
        timeline = probe(args.input, paths, config)
        print(paths.proposed_timeline)
        return 0
    if args.command == "analyze":
        timeline = read_json(args.timeline)
        proposed = analyze(args.input, timeline, config)
        write_json(args.out, proposed)
        print(args.out)
        return 0
    if args.command == "accept":
        timeline = read_json(args.timeline)
        accepted = set_operation_state(timeline, args.operation_id, "accepted")
        for op in accepted.get("operations", []):
            if op["state"] == "accepted":
                op["preview_ref"] = op.get("preview_ref") or "preview/before-after-preview.mp3"
                op["diff_ref"] = op.get("diff_ref") or "diff/timeline-diff.json"
                op["recovery_ref"] = op.get("recovery_ref") or "recovery/recovery-map.json"
        write_json(args.out, accepted)
        print(args.out)
        return 0
    if args.command == "reject":
        rejected = set_operation_state(read_json(args.timeline), args.operation_id, "rejected")
        write_json(args.out, rejected)
        print(args.out)
        return 0
    if args.command == "review-accept":
        if not args.operation_id:
            print("review-accept requires at least one --operation-id", file=sys.stderr)
            return 1
        try:
            reviewed = review_accept_operations(read_json(args.timeline), args.operation_id, args.reviewer, args.note)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        write_json(args.out, reviewed)
        print(args.out)
        return 0
    if args.command == "undo":
        try:
            restored = undo_accepted_operations(read_json(args.timeline), args.operation_id, undo_all=args.all, reason=args.reason)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        write_json(args.out, restored)
        print(args.out)
        return 0
    if args.command == "render":
        timeline = read_json(args.timeline)
        try:
            select_export_profiles(args.export_profile or config.export_profiles)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if any(op.get("state") == "proposed" for op in timeline.get("operations", [])) and not args.accept_safe_defaults:
            print("render requires an accepted timeline; run accept first or pass --accept-safe-defaults for deterministic silence only", file=sys.stderr)
            return 1
        if args.accept_safe_defaults:
            timeline = accept_safe_defaults(timeline)
        unsafe_retakes = [op for op in timeline.get("operations", []) if op.get("state") == "accepted" and not retake_operation_is_render_safe(op)]
        if unsafe_retakes:
            print("accepted retake_cut operations must carry successful auto_accept_policy or explicit manual review", file=sys.stderr)
            return 1
        episode_id = args.episode_id or episode_id_from_path(args.input)
        paths = run_paths(args.out, episode_id)
        write_preview(paths, args.input, timeline)
        write_diff_artifacts(paths, timeline, timeline)
        write_recovery_artifacts(paths, timeline)
        try:
            rendered = render(args.input, paths, timeline, config, export_profile_names=args.export_profile)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        rendered = transcribe_and_write(paths, rendered)
        write_json(paths.accepted_timeline, rendered)
        print(paths.accepted_timeline)
        return 0
    if args.command == "run":
        transcript_segments = None
        if args.transcript_json:
            try:
                transcript_segments = _load_optional_transcript(args.transcript_json)
            except (OSError, TranscriptValidationError) as exc:
                print(str(exc), file=sys.stderr)
                return 1
        try:
            paths = run_pipeline(args.input, args.out, config, episode_id=args.episode_id, transcript_segments=transcript_segments, export_profile_names=args.export_profile)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(paths.root)
        return 0
    if args.command == "dry-run":
        try:
            transcript_segments = _load_optional_transcript(args.transcript_json)
        except (OSError, TranscriptValidationError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        episode_id = args.episode_id or episode_id_from_path(args.input)
        paths = run_paths(args.out, episode_id)
        timeline = probe(args.input, paths, config)
        proposed = analyze(args.input, timeline, config)
        if transcript_segments:
            proposed = add_retake_proposals(proposed, transcript_segments, config, artifacts_exist=False)
        write_json(paths.proposed_timeline, proposed)
        ensure_run_dirs(paths)
        write_preview(paths, args.input, proposed)
        accepted = accept_safe_defaults(proposed)
        write_diff_artifacts(paths, proposed, accepted)
        write_recovery_artifacts(paths, accepted)
        accepted = transcribe_and_write(paths, accepted, cues=transcript_segments or [])
        write_json(paths.accepted_timeline, accepted)
        write_manifest(paths, {"input": str(args.input), "episode_id": episode_id, "dry_run": True, "artifacts": {"accepted_timeline": str(paths.accepted_timeline), "transcript": str(paths.transcript)}, "config": config_to_dict(config)})
        print(paths.root)
        return 0
    if args.command == "report":
        report = _build_run_report(args.run_dir)
        if args.format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(_format_run_report_markdown(report), end="")
        return 0
    if args.command == "review-list":
        review = _build_review_list(args.timeline, read_json(args.timeline))
        if args.format == "json":
            print(json.dumps(review, indent=2, ensure_ascii=False))
        else:
            print(_format_review_list_markdown(review), end="")
        return 0
    if args.command == "explain":
        try:
            explanation = explain_operation(read_json(args.timeline), args.operation_id)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(explanation, indent=2, ensure_ascii=False))
        else:
            print(format_explanation_markdown(explanation), end="")
        return 0
    if args.command == "validate-transcript":
        try:
            segments = load_transcript_segments(args.transcript_json)
        except (OSError, TranscriptValidationError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"ok ({len(segments)} segments)")
        return 0
    if args.command == "validate":
        errors = validate_timeline(read_json(args.timeline))
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("ok")
        return 0
    if args.command == "demo-fixtures":
        paths = make_demo_fixtures(args.out)
        for kind, path in paths.items():
            print(f"{kind}: {path}")
        return 0
    parser.error("unreachable")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
