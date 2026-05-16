from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ai_resources import format_ai_resource_profiles_markdown, get_ai_resource_profile, list_ai_resource_profiles
from .ai_doctor import build_ai_doctor_report, format_ai_doctor_markdown
from .ai_models import build_model_catalog, build_model_readiness_report, build_pull_plan, format_model_catalog_markdown, format_model_readiness_markdown, format_pull_plan_script
from .ai_drafts import AI_DRAFT_REL_PATH, AIServiceError, build_ai_explanation, generate_ai_draft
from .asr import ASRProviderError, provider_names, transcribe_to_file
from .artifacts import ensure_run_dirs, run_paths, write_diff_artifacts, write_manifest, write_recovery_artifacts
from .config import ConfigValidationError, config_to_dict, load_config
from .explain import explain_operation, format_explanation_markdown
from .exports import select_export_profiles
from .fixtures import make_demo_fixtures
from .html_report import build_html_report, write_html_report
from .local_review_server import serve_review_app, validate_review_host, write_review_launcher
from .pipeline import accept_safe_defaults, add_retake_proposals, analyze, episode_id_from_path, probe, render, retake_operation_is_render_safe, review_accept_operations, run_pipeline, transcribe_and_write, undo_accepted_operations, write_preview
from .project import build_batch_report, failed_episode, init_project, successful_episode, write_batch_reports
from .review_session import apply_decision, format_next_review_markdown, format_review_status_markdown, next_review_item, replay_review_session, review_status, write_review_session
from .transcript import TranscriptValidationError, load_transcript_segments
from .diarization import DiarizationError, diarize_to_file
from .recipe import RecipeError, apply_recipe, export_recipe
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
    p_report.add_argument("--format", choices=("json", "markdown", "html"), default="markdown")

    p_html_report = sub.add_parser("html-report", help="Write a static local HTML report for a run directory")
    p_html_report.add_argument("run_dir")
    p_html_report.add_argument("--out", required=True)

    p_review_list = sub.add_parser("review-list", help="List timeline operations with preview refs for producer review")
    p_review_list.add_argument("timeline")
    p_review_list.add_argument("--format", choices=("json", "markdown"), default="markdown")

    p_review = sub.add_parser("review", help="Review session commands")
    review_sub = p_review.add_subparsers(dest="review_command", required=True)
    p_review_status = review_sub.add_parser("status", help="Summarize a review session")
    p_review_status.add_argument("session")
    p_review_status.add_argument("--format", choices=("json", "markdown"), default="markdown")
    p_review_decide = review_sub.add_parser("decide", help="Append an accept/reject/undo review decision")
    p_review_decide.add_argument("session")
    p_review_decide.add_argument("--operation-id", required=True)
    p_review_decide.add_argument("--decision", choices=("accept", "reject", "undo"), required=True)
    p_review_decide.add_argument("--reviewer", required=True)
    p_review_decide.add_argument("--note", default="")
    p_review_decide.add_argument("--decided-at")
    p_review_rebuild = review_sub.add_parser("rebuild", help="Replay a review session onto a proposed timeline")
    p_review_rebuild.add_argument("session")
    p_review_rebuild.add_argument("--timeline", required=True)
    p_review_rebuild.add_argument("--out", required=True)
    p_review_next = review_sub.add_parser("next", help="Show the next operation needing review")
    p_review_next.add_argument("session")
    p_review_next.add_argument("--timeline", required=True)
    p_review_next.add_argument("--format", choices=("json", "markdown"), default="markdown")
    p_review_serve = review_sub.add_parser("serve", help="Run a localhost review UI for a run directory")
    p_review_serve.add_argument("run_dir")
    p_review_serve.add_argument("--host", default="127.0.0.1")
    p_review_serve.add_argument("--port", type=int, default=8765)
    p_review_launcher = review_sub.add_parser("launcher", help="Write a local launcher for the review UI")
    p_review_launcher.add_argument("run_dir")
    p_review_launcher.add_argument("--out", required=True)
    p_review_launcher.add_argument("--desktop-out")
    p_review_launcher.add_argument("--host", default="127.0.0.1")
    p_review_launcher.add_argument("--port", type=int, default=8765)

    p_explain = sub.add_parser("explain", help="Explain one timeline operation with detector evidence and review requirements")
    p_explain.add_argument("timeline")
    p_explain.add_argument("--operation-id", required=True)
    p_explain.add_argument("--with-ai", action="store_true", help="Include local AI explanation fields")
    p_explain.add_argument("--dry-prompt", action="store_true", help="Build AI request payload without network call")
    p_explain.add_argument("--no-net", action="store_true", help="Disable AI network call")
    p_explain.add_argument("--base-url", help="AI base URL (OpenAI-compatible)")
    p_explain.add_argument("--model", help="AI model name")
    p_explain.add_argument("--timeout", type=float, default=0.5)
    p_explain.add_argument("--transcript-json", help="Optional transcript JSON for AI explanation context")
    p_explain.add_argument("--format", choices=("json", "markdown"), default="markdown")

    p_project = sub.add_parser("project", help="Project manifest commands")
    project_sub = p_project.add_subparsers(dest="project_command", required=True)
    p_project_init = project_sub.add_parser("init", help="Create a local project manifest")
    p_project_init.add_argument("project_dir")
    p_project_init.add_argument("--name")

    p_batch = sub.add_parser("batch", help="Batch processing commands")
    batch_sub = p_batch.add_subparsers(dest="batch_command", required=True)
    p_batch_dry_run = batch_sub.add_parser("dry-run", help="Run dry-run over multiple inputs and write aggregate reports")
    p_batch_dry_run.add_argument("inputs", nargs="+")
    p_batch_dry_run.add_argument("--out", default="runs")
    p_batch_dry_run.add_argument("--fail-fast", action="store_true")

    p_diarize = sub.add_parser("diarize", help="Generate speaker_segments.v1 from audio via a diarization provider")
    p_diarize.add_argument("input", help="Source audio path")
    p_diarize.add_argument("--provider", default="mock", choices=("mock", "pyannote"), help="Diarization provider (mock ships offline; pyannote requires HF_TOKEN and is deferred to PR-C2)")
    p_diarize.add_argument("--out", required=True, help="Output path for speaker_segments.v1.json")
    p_diarize.add_argument("--config", help="Path to provider config JSON (mock provider: list of segments to return)")

    p_recipe = sub.add_parser("recipe", help="Export or apply a portable recipe.v1 of a run directory")
    recipe_sub = p_recipe.add_subparsers(dest="recipe_command", required=True)
    p_recipe_export = recipe_sub.add_parser("export", help="Bundle a run directory into recipe.v1.json")
    p_recipe_export.add_argument("--run", required=True, help="Run directory produced by `run` or `dry-run`")
    p_recipe_export.add_argument("--out", required=True, help="Output recipe path")
    p_recipe_apply = recipe_sub.add_parser("apply", help="Replay a recipe against source media into a new run directory")
    p_recipe_apply.add_argument("--recipe", required=True, help="Recipe JSON path")
    p_recipe_apply.add_argument("--media", required=True, help="Source media path; must match recipe sha256 unless --allow-media-drift")
    p_recipe_apply.add_argument("--out", required=True, help="Output run directory")
    p_recipe_apply.add_argument("--allow-media-drift", action="store_true", help="Skip source media sha256 verification")

    p_transcribe = sub.add_parser("transcribe", help="Generate transcript JSON with a local provider")
    p_transcribe.add_argument("input")
    p_transcribe.add_argument("--provider", default="stub", help=f"Transcript provider (available: {', '.join(provider_names())})")
    p_transcribe.add_argument("--model", help="Optional ASR model name or path for providers that need it")
    p_transcribe.add_argument("--device", help="Optional ASR device, for example cuda or cpu")
    p_transcribe.add_argument("--compute-type", help="Optional ASR compute type, for example float16 or int8_float16")
    p_transcribe.add_argument("--binary", help="Optional local ASR executable path, for example whisper.cpp whisper-cli")
    p_transcribe.add_argument("--model-path", help="Optional local ASR model file path, for example ggml-large-v3-q5_0.bin")
    p_transcribe.add_argument("--language", help="Optional ASR language code, for example zh or en")
    p_transcribe.add_argument("--threads", type=int, help="Optional ASR thread count for local providers")
    p_transcribe.add_argument("--out", required=True)

    p_ai = sub.add_parser("ai", help="AI resource and adapter commands")
    ai_sub = p_ai.add_subparsers(dest="ai_command", required=True)
    p_ai_resources = ai_sub.add_parser("resources", help="Show local-first AI resource profiles")
    p_ai_resources.add_argument("--profile")
    p_ai_resources.add_argument("--format", choices=("json", "markdown"), default="markdown")
    p_ai_doctor = ai_sub.add_parser("doctor", help="Check local AI environment wiring without downloading models")
    p_ai_doctor.add_argument("--compose-file", default="compose.yaml")
    p_ai_doctor.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    p_ai_doctor.add_argument("--no-ollama", action="store_true", help="Skip the timeout-bounded Ollama connectivity check")
    p_ai_doctor.add_argument("--timeout", type=float, default=0.5, help="Ollama connectivity timeout in seconds")
    p_ai_doctor.add_argument("--whisper-binary")
    p_ai_doctor.add_argument("--whisper-model")
    p_ai_doctor.add_argument("--optional-whisper", action="store_true", help="Treat missing whisper.cpp paths as warnings")
    p_ai_doctor.add_argument("--format", choices=("json", "markdown"), default="markdown")
    p_ai_models = ai_sub.add_parser("models", help="Show local model catalog and manual pull plans")
    p_ai_models.add_argument("--tier", default="all", choices=("all", "api-local", "smoke", "recommended", "heavy-manual"))
    p_ai_models.add_argument("--pull-plan", action="store_true", help="Print manual Ollama pull commands without executing them")
    p_ai_models.add_argument("--readiness", action="store_true", help="Compare catalog models against installed API/Ollama model lists")
    p_ai_models.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    p_ai_models.add_argument("--ollama-tags-json")
    p_ai_models.add_argument("--no-ollama", action="store_true")
    p_ai_models.add_argument("--openai-base-url")
    p_ai_models.add_argument("--openai-models-json")
    p_ai_models.add_argument("--no-openai-api", action="store_true")
    p_ai_models.add_argument("--timeout", type=float, default=0.5)
    p_ai_models.add_argument("--format", choices=("json", "markdown"), default="markdown")
    p_ai_draft = ai_sub.add_parser("draft", help="Generate AI drafting suggestions from timeline and transcript")
    p_ai_draft.add_argument("--timeline", required=True)
    p_ai_draft.add_argument("--transcript-json")
    p_ai_draft.add_argument("--out")
    p_ai_draft.add_argument("--dry-prompt", action="store_true", help="Build payload only, no network call")
    p_ai_draft.add_argument("--dry-run", action="store_true", help="Alias for --dry-prompt; do not send network request")
    p_ai_draft.add_argument("--no-net", action="store_true", help="Skip AI request")
    p_ai_draft.add_argument("--base-url", help="AI base URL (OpenAI-compatible)")
    p_ai_draft.add_argument("--model", help="AI model name")
    p_ai_draft.add_argument("--timeout", type=float, default=0.5)
    p_ai_draft.add_argument("--max-chapters", type=int, default=8)
    p_ai_draft.add_argument("--speaker-segments", help="Optional speaker_segments.v1.json for per-speaker attribution")
    p_ai_draft.add_argument("--speaker-label", action="append", default=[], help="Map speaker id to display label, e.g. spk0=Host. Repeatable.")
    p_ai_draft.add_argument("--format", choices=("json", "markdown"), default="json")

    p_validate_transcript = sub.add_parser("validate-transcript", help="Validate transcript JSON import shape")
    p_validate_transcript.add_argument("transcript_json")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("timeline")

    p_validate_run = sub.add_parser("validate-run", help="Preflight config, timeline, and transcript inputs together")
    p_validate_run.add_argument("--config", help="Optional JSON config path")
    p_validate_run.add_argument("--timeline", help="Optional timeline JSON path")
    p_validate_run.add_argument("--transcript-json", help="Optional transcript JSON path")
    p_validate_run.add_argument("--duration", type=float, help="Optional media duration override for transcript bounds")

    p_demo = sub.add_parser("demo-fixtures", help="Generate deterministic demo media fixtures with ffmpeg when available")
    p_demo.add_argument("--out", default="demo-fixtures")
    return parser


def _load_review_session_or_empty(session_path: str | Path, source_timeline: str | Path | None = None) -> dict:
    """Read a review-session.json or return an empty session dict.

    Matches `local_review_server.load_review_context` semantics: review CLI
    subcommands (`next`, `status`, `decide`) must work against a freshly
    completed `run` directory where `review-session.json` has not been seeded
    yet, instead of crashing with FileNotFoundError.
    """
    path = Path(session_path)
    if path.exists():
        return read_json(path)
    return {
        "schema_version": "review-session.v1",
        "source_timeline": str(source_timeline) if source_timeline else "",
        "decisions": [],
    }


def _load_optional_transcript(path: str | None) -> list[dict] | None:
    if not path:
        return None
    return load_transcript_segments(path)


def _resolve_ai_output_path(timeline_path: str | Path, out: str | None) -> Path:
    timeline_dir = Path(timeline_path).parent
    if not out:
        return timeline_dir / AI_DRAFT_REL_PATH
    candidate = Path(out)
    if candidate.suffix.lower() == ".json":
        return candidate
    return candidate / AI_DRAFT_REL_PATH


def _execute_dry_run(input_path: str | Path, out_dir: str | Path, config, episode_id: str | None = None, transcript_segments: list[dict] | None = None):
    episode = episode_id or episode_id_from_path(input_path)
    paths = run_paths(out_dir, episode)
    timeline = probe(input_path, paths, config)
    proposed = analyze(input_path, timeline, config)
    if transcript_segments:
        proposed = add_retake_proposals(proposed, transcript_segments, config, artifacts_exist=False)
    write_json(paths.proposed_timeline, proposed)
    ensure_run_dirs(paths)
    write_preview(paths, input_path, proposed)
    accepted = accept_safe_defaults(proposed)
    write_diff_artifacts(paths, proposed, accepted)
    write_recovery_artifacts(paths, accepted)
    accepted = transcribe_and_write(paths, accepted, cues=transcript_segments or [])
    write_json(paths.accepted_timeline, accepted)
    write_manifest(paths, {"input": str(input_path), "episode_id": episode, "dry_run": True, "artifacts": {"accepted_timeline": str(paths.accepted_timeline), "transcript": str(paths.transcript)}, "config": config_to_dict(config)})
    return paths


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


def _validate_transcript_duration(segments: list[dict], duration: float) -> list[str]:
    errors = []
    for idx, segment in enumerate(segments):
        if float(segment["end"]) > duration:
            errors.append(f"segment[{idx}] ends after media duration ({segment['end']} > {duration})")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
    except (OSError, json.JSONDecodeError, ConfigValidationError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
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
        paths = _execute_dry_run(args.input, args.out, config, episode_id=args.episode_id, transcript_segments=transcript_segments)
        print(paths.root)
        return 0
    if args.command == "report":
        if args.format == "html":
            print(build_html_report(args.run_dir), end="")
            return 0
        report = _build_run_report(args.run_dir)
        if args.format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(_format_run_report_markdown(report), end="")
        return 0
    if args.command == "html-report":
        write_html_report(args.run_dir, args.out)
        print(args.out)
        return 0
    if args.command == "review-list":
        review = _build_review_list(args.timeline, read_json(args.timeline))
        if args.format == "json":
            print(json.dumps(review, indent=2, ensure_ascii=False))
        else:
            print(_format_review_list_markdown(review), end="")
        return 0
    if args.command == "review":
        if args.review_command == "status":
            status = review_status(_load_review_session_or_empty(args.session))
            if args.format == "json":
                print(json.dumps(status, indent=2, ensure_ascii=False))
            else:
                print(format_review_status_markdown(status), end="")
            return 0
        if args.review_command == "decide":
            try:
                session = apply_decision(
                    _load_review_session_or_empty(args.session),
                    args.operation_id,
                    args.decision,
                    args.reviewer,
                    note=args.note,
                    decided_at=args.decided_at,
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            write_review_session(args.session, session)
            print(args.session)
            return 0
        if args.review_command == "rebuild":
            try:
                rebuilt = replay_review_session(read_json(args.timeline), read_json(args.session))
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            write_json(args.out, rebuilt)
            print(args.out)
            return 0
        if args.review_command == "next":
            item = next_review_item(
                read_json(args.timeline),
                _load_review_session_or_empty(args.session, source_timeline=args.timeline),
                session_path=args.session,
            )
            if args.format == "json":
                print(json.dumps(item, indent=2, ensure_ascii=False))
            else:
                print(format_next_review_markdown(item), end="")
            return 0
        if args.review_command == "serve":
            try:
                validate_review_host(args.host)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            serve_review_app(args.run_dir, host=args.host, port=args.port)
            return 0
        if args.review_command == "launcher":
            try:
                result = write_review_launcher(args.run_dir, args.out, desktop_out=args.desktop_out, host=args.host, port=args.port)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            print(result["script"])
            return 0
    if args.command == "explain":
        try:
            if args.with_ai:
                timeline = read_json(args.timeline)
                transcript_segments = _load_optional_transcript(args.transcript_json)
                explanation = build_ai_explanation(
                    timeline=timeline,
                    operation_id=args.operation_id,
                    transcript_segments=transcript_segments,
                    base_url=args.base_url,
                    model=args.model,
                    timeout_s=args.timeout,
                    dry_prompt=args.dry_prompt,
                    no_net=args.no_net,
                )
            else:
                explanation = explain_operation(read_json(args.timeline), args.operation_id)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(explanation, indent=2, ensure_ascii=False))
        else:
            print(format_explanation_markdown(explanation), end="")
        return 0
    if args.command == "project":
        if args.project_command == "init":
            manifest_path = init_project(args.project_dir, name=args.name)
            print(manifest_path)
            return 0
    if args.command == "batch":
        if args.batch_command == "dry-run":
            episodes = []
            for input_path in args.inputs:
                try:
                    paths = _execute_dry_run(input_path, args.out, config)
                    episodes.append(successful_episode(input_path, paths.root, _build_run_report(paths.root)))
                except (OSError, ValueError) as exc:
                    episodes.append(failed_episode(input_path, exc))
                    if args.fail_fast:
                        break
            report = build_batch_report(episodes, args.out)
            report_json, _ = write_batch_reports(args.out, report)
            print(report_json)
            return 1 if report["summary"]["failed"] else 0
    if args.command == "ai":
        if args.ai_command == "resources":
            try:
                if args.profile:
                    payload = {"default_profile": "rtx4090-local", "profiles": [get_ai_resource_profile(args.profile)]}
                else:
                    payload = list_ai_resource_profiles()
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            if args.format == "json":
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print(format_ai_resource_profiles_markdown(payload))
            return 0
        if args.ai_command == "doctor":
            report = build_ai_doctor_report(
                compose_file=args.compose_file,
                whisper_binary=args.whisper_binary,
                whisper_model=args.whisper_model,
                ollama_url=args.ollama_url,
                check_ollama=not args.no_ollama,
                timeout_s=args.timeout,
                require_whisper=not args.optional_whisper,
            )
            if args.format == "json":
                print(json.dumps(report, indent=2, ensure_ascii=False))
            else:
                print(format_ai_doctor_markdown(report), end="")
            return 1 if report["overall_status"] == "missing" else 0
        if args.ai_command == "draft":
            if not args.transcript_json:
                print("ai draft requires --transcript-json", file=sys.stderr)
                return 1
            try:
                transcript_segments = _load_optional_transcript(args.transcript_json)
                timeline = read_json(args.timeline)
            except (OSError, json.JSONDecodeError, TranscriptValidationError) as exc:
                print(str(exc), file=sys.stderr)
                return 1
            timeline_errors = validate_timeline(timeline)
            if timeline_errors:
                for error in timeline_errors:
                    print(error, file=sys.stderr)
                return 1
            speaker_segments_payload = None
            if args.speaker_segments:
                try:
                    raw_segments = read_json(args.speaker_segments)
                except (OSError, json.JSONDecodeError) as exc:
                    print(str(exc), file=sys.stderr)
                    return 1
                if isinstance(raw_segments, dict) and isinstance(raw_segments.get("segments"), list):
                    speaker_segments_payload = raw_segments["segments"]
                elif isinstance(raw_segments, list):
                    speaker_segments_payload = raw_segments
                else:
                    print("--speaker-segments expects speaker_segments.v1 JSON (object with segments array, or raw list)", file=sys.stderr)
                    return 1
            speaker_labels_payload: dict[str, str] | None = None
            if args.speaker_label:
                labels: dict[str, str] = {}
                for entry in args.speaker_label:
                    if "=" not in entry:
                        print(f"--speaker-label expects spk0=Host form: {entry!r}", file=sys.stderr)
                        return 1
                    key, value = entry.split("=", 1)
                    labels[key.strip()] = value.strip()
                speaker_labels_payload = labels
            try:
                payload = generate_ai_draft(
                    timeline=timeline,
                    transcript_segments=transcript_segments,
                    base_url=args.base_url,
                    model=args.model,
                    timeout_s=args.timeout,
                    max_chapters=args.max_chapters,
                    dry_prompt=args.dry_prompt or args.dry_run,
                    no_net=args.no_net or args.dry_run,
                    timeline_path=args.timeline,
                    speaker_segments=speaker_segments_payload,
                    speaker_labels=speaker_labels_payload,
                )
            except (OSError, json.JSONDecodeError, TranscriptValidationError, AIServiceError, ValueError) as exc:
                print(str(exc), file=sys.stderr)
                return 1
            out_path = _resolve_ai_output_path(args.timeline, args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(out_path, payload)
            if args.format == "json":
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print(f"AI draft: {out_path}")
            return 0
        if args.ai_command == "models":
            if args.readiness:
                report = build_model_readiness_report(
                    tier=args.tier,
                    tags_json=args.ollama_tags_json,
                    openai_models_json=args.openai_models_json,
                    ollama_url=args.ollama_url,
                    openai_base_url=args.openai_base_url,
                    timeout_s=args.timeout,
                    check_ollama=not args.no_ollama,
                    check_openai_api=not args.no_openai_api,
                )
                if args.format == "json":
                    print(json.dumps(report, indent=2, ensure_ascii=False))
                else:
                    print(format_model_readiness_markdown(report), end="")
                return 0
            if args.pull_plan:
                plan = build_pull_plan(tier=args.tier if args.tier != "all" else "smoke")
                if args.format == "json":
                    print(json.dumps(plan, indent=2, ensure_ascii=False))
                else:
                    print(format_pull_plan_script(plan), end="")
                return 0
            catalog = build_model_catalog(tier=args.tier)
            if args.format == "json":
                print(json.dumps(catalog, indent=2, ensure_ascii=False))
            else:
                print(format_model_catalog_markdown(catalog), end="")
            return 0
    if args.command == "diarize":
        try:
            out = diarize_to_file(args.input, args.out, provider=args.provider, config_path=args.config)
        except DiarizationError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(out)
        return 0
    if args.command == "recipe":
        if args.recipe_command == "export":
            try:
                path = export_recipe(args.run, args.out)
            except RecipeError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            print(path)
            return 0
        if args.recipe_command == "apply":
            try:
                out = apply_recipe(
                    args.recipe,
                    args.media,
                    args.out,
                    allow_media_drift=args.allow_media_drift,
                )
            except RecipeError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            print(out)
            return 0
    if args.command == "transcribe":
        try:
            options = {
                key: value
                for key, value in {
                    "model": args.model,
                    "device": args.device,
                    "compute_type": args.compute_type,
                    "binary": args.binary,
                    "model_path": args.model_path,
                    "language": args.language,
                    "threads": args.threads,
                }.items()
                if value is not None
            }
            transcript_path = transcribe_to_file(args.input, args.out, provider_name=args.provider, **options)
        except ASRProviderError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(transcript_path)
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
    if args.command == "validate-run":
        errors: list[str] = []
        checked: list[str] = []
        duration = args.duration

        if args.config:
            checked.append("config")

        if args.timeline:
            checked.append("timeline")
            try:
                timeline = read_json(args.timeline)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"timeline: {exc}")
            else:
                errors.extend(validate_timeline(timeline))
                if duration is None:
                    raw_duration = timeline.get("media_manifest", {}).get("duration") if isinstance(timeline, dict) else None
                    if raw_duration is not None:
                        duration = float(raw_duration)

        transcript_count = None
        if args.transcript_json:
            checked.append("transcript")
            try:
                segments = load_transcript_segments(args.transcript_json)
            except (OSError, TranscriptValidationError) as exc:
                errors.append(str(exc))
            else:
                transcript_count = len(segments)
                if duration is not None:
                    errors.extend(_validate_transcript_duration(segments, duration))

        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        if not checked:
            print("validate-run requires at least one of --config, --timeline, or --transcript-json", file=sys.stderr)
            return 1
        summary = [f"ok: {', '.join(checked)}"]
        if transcript_count is not None:
            suffix = "segment" if transcript_count == 1 else "segments"
            summary.append(f"transcript: {transcript_count} {suffix}")
        if duration is not None:
            summary.append(f"duration: {duration:g}s")
        print("; ".join(summary))
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
