from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .timeline import write_json

PROJECT_MANIFEST_NAME = "podcast-project.v1.json"
BATCH_REPORT_JSON = "batch-report.json"
BATCH_REPORT_MARKDOWN = "batch-report.md"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def init_project(project_dir: str | Path, name: str | None = None, created_at: str | None = None) -> Path:
    root = Path(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / PROJECT_MANIFEST_NAME
    manifest = {
        "schema_version": "podcast-project.v1",
        "name": name or root.name,
        "project_dir": str(root),
        "created_at": created_at or utc_now(),
        "episodes": [],
    }
    write_json(manifest_path, manifest)
    return manifest_path


def _quality_state(quality_gate: object) -> str:
    if not isinstance(quality_gate, dict):
        return "not_measured"
    return "passed" if quality_gate.get("passed") is True else "failed"


def successful_episode(input_path: str | Path, run_dir: str | Path, run_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "input": str(input_path),
        "episode_id": Path(run_dir).name,
        "run_dir": str(run_dir),
        "status": "succeeded",
        "operation_counts": run_report.get("operation_counts", {}),
        "total_removed_duration": float(run_report.get("total_removed_duration") or 0.0),
        "quality_state": _quality_state(run_report.get("quality_gate")),
        "warnings": list(run_report.get("warnings") or []),
    }


def failed_episode(input_path: str | Path, error: BaseException | str) -> dict[str, Any]:
    return {
        "input": str(input_path),
        "episode_id": Path(input_path).stem,
        "run_dir": None,
        "status": "failed",
        "error": str(error),
        "operation_counts": {},
        "total_removed_duration": 0.0,
        "quality_state": "not_measured",
        "warnings": [],
    }


def build_batch_report(episodes: list[dict[str, Any]], out_dir: str | Path) -> dict[str, Any]:
    succeeded = sum(1 for episode in episodes if episode.get("status") == "succeeded")
    failed = sum(1 for episode in episodes if episode.get("status") == "failed")
    quality_states: dict[str, int] = {}
    for episode in episodes:
        state = str(episode.get("quality_state") or "not_measured")
        quality_states[state] = quality_states.get(state, 0) + 1
    return {
        "schema_version": "batch-report.v1",
        "out_dir": str(out_dir),
        "summary": {
            "total": len(episodes),
            "succeeded": succeeded,
            "failed": failed,
        },
        "total_removed_duration": sum(float(episode.get("total_removed_duration") or 0.0) for episode in episodes),
        "quality_states": dict(sorted(quality_states.items())),
        "episodes": episodes,
    }


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def format_batch_report_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# Batch Dry-run Report",
        "",
        f"Output directory: {report.get('out_dir')}",
        "",
        "## Summary",
        "",
        f"- Total episodes: {summary.get('total', 0)}",
        f"- Succeeded: {summary.get('succeeded', 0)}",
        f"- Failed: {summary.get('failed', 0)}",
        f"- Total removed duration: {float(report.get('total_removed_duration') or 0.0):.3f}s",
        "",
        "## Episodes",
        "",
        "| Episode | Status | Removed | Quality | Warnings | Error |",
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for episode in report.get("episodes") or []:
        warnings = len(episode.get("warnings") or [])
        error = episode.get("error") or "-"
        lines.append(
            f"| {_markdown_cell(episode.get('episode_id') or '-')} | {_markdown_cell(episode.get('status') or '-')} | "
            f"{float(episode.get('total_removed_duration') or 0.0):.3f}s | "
            f"{_markdown_cell(episode.get('quality_state') or '-')} | {warnings} | {_markdown_cell(error)} |"
        )
    return "\n".join(lines) + "\n"


def write_batch_reports(out_dir: str | Path, report: dict[str, Any]) -> tuple[Path, Path]:
    batch_dir = Path(out_dir) / "batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    json_path = batch_dir / BATCH_REPORT_JSON
    markdown_path = batch_dir / BATCH_REPORT_MARKDOWN
    write_json(json_path, report)
    markdown_path.write_text(format_batch_report_markdown(report), encoding="utf-8")
    return json_path, markdown_path
