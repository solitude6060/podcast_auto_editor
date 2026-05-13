from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from .review_session import review_status
from .timeline import read_json


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _rel_link(root: Path, value: str | None) -> str | None:
    if not value:
        return None
    path = Path(value)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return value.replace("\\", "/")


def _link(root: Path, value: str | None, label: str) -> str:
    href = _rel_link(root, value)
    if not href:
        return "-"
    return f'<a href="{_escape(href)}">{_escape(label)}</a>'


def _load_run(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    timeline_path = root / "timeline.accepted.v1.json"
    diff_path = root / "diff" / "timeline-diff.json"
    timeline = read_json(timeline_path) if timeline_path.exists() else {}
    diff = read_json(diff_path) if diff_path.exists() else {}
    return timeline, diff


def _operation_needs_manual_review(op: dict[str, Any]) -> bool:
    if op.get("type") not in {"speech_cut", "retake_cut"}:
        return False
    provenance = op.get("provenance") or {}
    manual_review = provenance.get("manual_review")
    auto_policy = str(provenance.get("auto_accept_policy", ""))
    return not (isinstance(manual_review, dict) and manual_review.get("decision") == "accepted") and not auto_policy.startswith("accepted")


def _operation_rows(root: Path, operations: list[dict[str, Any]]) -> str:
    if not operations:
        return '<tr><td colspan="10">No operations</td></tr>'
    rows = []
    for op in operations:
        source = op.get("source_range") or {}
        provenance = op.get("provenance") or {}
        needs_review = _operation_needs_manual_review(op)
        row_class = ' class="manual-review-required"' if needs_review else ""
        review_label = "Manual review required" if needs_review else "Review optional"
        rows.append(
            f"<tr{row_class}>"
            f"<td>{_escape(op.get('operation_id'))}</td>"
            f"<td>{_escape(op.get('type'))}</td>"
            f"<td>{_escape(op.get('state'))}</td>"
            f"<td>{_escape(op.get('risk'))}</td>"
            f"<td>{_escape(op.get('confidence'))}</td>"
            f"<td>{_escape(source.get('start'))}-{_escape(source.get('end'))}</td>"
            f"<td>{_escape(provenance.get('detector') or 'unknown')}</td>"
            f"<td>{_escape(review_label)}</td>"
            f"<td>{_link(root, op.get('preview_ref'), 'preview')}</td>"
            f"<td>{_link(root, op.get('diff_ref'), 'diff')} / {_link(root, op.get('recovery_ref'), 'recovery')}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _count_by(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _group_list(values: dict[str, int]) -> str:
    if not values:
        return "<li>none</li>"
    return "".join(f"<li>{_escape(key)}: {_escape(value)}</li>" for key, value in values.items())


def _review_session_summary(root: Path, operation_count: int) -> str:
    session_path = root / "review-session.json"
    if not session_path.exists():
        return "<p>No review session found.</p>"
    status = review_status(read_json(session_path), total_operations=operation_count)
    counts = status.get("decision_counts", {})
    return (
        f"<p>{_link(root, str(session_path), 'review-session.json')}</p>"
        "<ul>"
        f"<li>Accepted: {_escape(counts.get('accepted', 0))}</li>"
        f"<li>Rejected: {_escape(counts.get('rejected', 0))}</li>"
        f"<li>Undone: {_escape(counts.get('undone', 0))}</li>"
        f"<li>Pending: {_escape(counts.get('pending', 0))}</li>"
        "</ul>"
    )


def _export_rows(root: Path, profiles: list[dict[str, Any]]) -> str:
    if not profiles:
        return '<tr><td colspan="3">No export profiles</td></tr>'
    rows = []
    for profile in profiles:
        gate = profile.get("quality_gate_report") or {}
        rows.append(
            "<tr>"
            f"<td>{_escape(profile.get('name'))}</td>"
            f"<td>{_escape(gate.get('passed', 'not measured'))}</td>"
            f"<td>{_link(root, profile.get('path'), 'file')}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def build_html_report(run_dir: str | Path) -> str:
    root = Path(run_dir)
    timeline, diff = _load_run(root)
    export_metadata = timeline.get("export_metadata") or {}
    derived = export_metadata.get("derived_assets") or {}
    warnings = []
    for key in ("cue_errors", "chapter_errors"):
        warnings.extend(derived.get(key, []) or [])
    operations = timeline.get("operations") if isinstance(timeline.get("operations"), list) else []
    profiles = export_metadata.get("export_profiles") if isinstance(export_metadata.get("export_profiles"), list) else []
    risk_groups = _count_by([str(op.get("risk") or "unknown") for op in operations])
    detector_groups = _count_by([str((op.get("provenance") or {}).get("detector") or "unknown") for op in operations])
    quality_gate = export_metadata.get("quality_gate_report")
    quality_summary = quality_gate.get("passed") if isinstance(quality_gate, dict) else "not measured"
    warning_items = "".join(f"<li>{_escape(warning)}</li>" for warning in warnings) or "<li>none</li>"
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Podcast Auto Editor Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.4; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.4rem; text-align: left; }}
    th {{ background: #f4f4f4; }}
    code {{ background: #f4f4f4; padding: 0.1rem 0.25rem; }}
    .manual-review-required {{ background: #fff4e5; }}
  </style>
</head>
<body>
  <h1>Podcast Auto Editor Report</h1>
  <p>Run directory: <code>{_escape(root)}</code></p>
  <section>
    <h2>Summary</h2>
    <ul>
      <li>Operations: {len(operations)}</li>
      <li>Proposed edits: {_escape(diff.get('proposed_count', 0))}</li>
      <li>Accepted edits: {_escape(diff.get('accepted_count', 0))}</li>
      <li>Rejected edits: {_escape(diff.get('rejected_count', 0))}</li>
      <li>Total removed duration: {_escape(diff.get('total_removed_duration', 0.0))}s</li>
      <li>Quality gate: {_escape(quality_summary)}</li>
    </ul>
  </section>
  <section>
    <h2>Operations</h2>
    <table>
      <thead><tr><th>ID</th><th>Type</th><th>State</th><th>Risk</th><th>Confidence</th><th>Source</th><th>Detector</th><th>Review</th><th>Preview</th><th>Artifacts</th></tr></thead>
      <tbody>{_operation_rows(root, operations)}</tbody>
    </table>
  </section>
  <section>
    <h2>Operation groups</h2>
    <h3>Risk</h3>
    <ul>{_group_list(risk_groups)}</ul>
    <h3>Detector</h3>
    <ul>{_group_list(detector_groups)}</ul>
  </section>
  <section>
    <h2>Review session</h2>
    {_review_session_summary(root, len(operations))}
  </section>
  <section>
    <h2>Export profiles</h2>
    <table>
      <thead><tr><th>Name</th><th>Quality passed</th><th>File</th></tr></thead>
      <tbody>{_export_rows(root, profiles)}</tbody>
    </table>
  </section>
  <section>
    <h2>Warnings</h2>
    <ul>{warning_items}</ul>
  </section>
</body>
</html>
'''


def write_html_report(run_dir: str | Path, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_html_report(run_dir))
