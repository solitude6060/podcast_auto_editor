from __future__ import annotations

import html
from pathlib import Path
from typing import Any

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


def _operation_rows(root: Path, operations: list[dict[str, Any]]) -> str:
    if not operations:
        return '<tr><td colspan="9">No operations</td></tr>'
    rows = []
    for op in operations:
        source = op.get("source_range") or {}
        provenance = op.get("provenance") or {}
        rows.append(
            "<tr>"
            f"<td>{_escape(op.get('operation_id'))}</td>"
            f"<td>{_escape(op.get('type'))}</td>"
            f"<td>{_escape(op.get('state'))}</td>"
            f"<td>{_escape(op.get('risk'))}</td>"
            f"<td>{_escape(op.get('confidence'))}</td>"
            f"<td>{_escape(source.get('start'))}-{_escape(source.get('end'))}</td>"
            f"<td>{_escape(provenance.get('detector') or 'unknown')}</td>"
            f"<td>{_link(root, op.get('preview_ref'), 'preview')}</td>"
            f"<td>{_link(root, op.get('diff_ref'), 'diff')} / {_link(root, op.get('recovery_ref'), 'recovery')}</td>"
            "</tr>"
        )
    return "\n".join(rows)


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
      <thead><tr><th>ID</th><th>Type</th><th>State</th><th>Risk</th><th>Confidence</th><th>Source</th><th>Detector</th><th>Preview</th><th>Artifacts</th></tr></thead>
      <tbody>{_operation_rows(root, operations)}</tbody>
    </table>
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
