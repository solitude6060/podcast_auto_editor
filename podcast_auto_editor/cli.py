from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifacts import run_paths, write_diff_artifacts, write_recovery_artifacts
from .config import load_config
from .pipeline import add_retake_proposals, analyze, episode_id_from_path, probe, render, run_pipeline, transcribe_and_write, write_preview
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

    p_render = sub.add_parser("render")
    p_render.add_argument("input")
    p_render.add_argument("--timeline", required=True)
    p_render.add_argument("--out", default="runs")
    p_render.add_argument("--episode-id")
    p_render.add_argument("--accept-safe-defaults", action="store_true", help="Accept deterministic silence cuts only before rendering")

    p_run = sub.add_parser("run")
    p_run.add_argument("input")
    p_run.add_argument("--out", default="runs")
    p_run.add_argument("--episode-id")
    p_run.add_argument("--transcript-json", help="Optional post-edit transcript segment JSON for MVP/stub runs")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("timeline")
    return parser


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
    if args.command == "render":
        timeline = read_json(args.timeline)
        if any(op.get("state") == "proposed" for op in timeline.get("operations", [])) and not args.accept_safe_defaults:
            print("render requires an accepted timeline; run accept first or pass --accept-safe-defaults for deterministic silence only", file=sys.stderr)
            return 1
        if args.accept_safe_defaults:
            from .pipeline import accept_safe_defaults
            timeline = accept_safe_defaults(timeline)
        unsafe_retakes = [op for op in timeline.get("operations", []) if op.get("type") == "retake_cut" and op.get("state") == "accepted" and not op.get("provenance", {}).get("auto_accept_policy", "").startswith("accepted")]
        if unsafe_retakes:
            print("accepted retake_cut operations must carry successful auto_accept_policy or be accepted through a future explicit review command", file=sys.stderr)
            return 1
        episode_id = args.episode_id or episode_id_from_path(args.input)
        paths = run_paths(args.out, episode_id)
        write_preview(paths, args.input, timeline)
        write_diff_artifacts(paths, timeline, timeline)
        write_recovery_artifacts(paths, timeline)
        rendered = render(args.input, paths, timeline, config)
        rendered = transcribe_and_write(paths, rendered)
        write_json(paths.accepted_timeline, rendered)
        print(paths.accepted_timeline)
        return 0
    if args.command == "run":
        transcript_segments = None
        if args.transcript_json:
            transcript_segments = json.loads(Path(args.transcript_json).read_text())
        paths = run_pipeline(args.input, args.out, config, episode_id=args.episode_id, transcript_segments=transcript_segments)
        print(paths.root)
        return 0
    if args.command == "validate":
        errors = validate_timeline(read_json(args.timeline))
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("ok")
        return 0
    parser.error("unreachable")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
