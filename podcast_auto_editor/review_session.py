from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .timeline import build_recovery, write_json

SCHEMA_VERSION = "review-session.v1"
VALID_DECISIONS = {"accept", "reject", "undo"}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_review_session(source_timeline: str | Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "source_timeline": str(source_timeline),
        "decisions": [],
    }


def apply_decision(
    session: dict[str, Any],
    operation_id: str,
    decision: str,
    reviewer: str,
    note: str = "",
    decided_at: str | None = None,
) -> dict[str, Any]:
    if decision not in VALID_DECISIONS:
        raise ValueError(f"decision must be one of: {', '.join(sorted(VALID_DECISIONS))}")
    reviewer = reviewer.strip()
    if not reviewer:
        raise ValueError("reviewer may not be empty")
    operation_id = operation_id.strip()
    if not operation_id:
        raise ValueError("operation_id may not be empty")
    updated = deepcopy(session)
    updated.setdefault("schema_version", SCHEMA_VERSION)
    updated.setdefault("decisions", []).append(
        {
            "operation_id": operation_id,
            "decision": decision,
            "reviewer": reviewer,
            "note": note,
            "decided_at": decided_at or _now(),
        }
    )
    return updated


def _attach_artifact_refs(operation: dict[str, Any]) -> None:
    operation["preview_ref"] = operation.get("preview_ref") or f"preview/operations/{operation.get('operation_id')}/before-after.mp3"
    operation["diff_ref"] = operation.get("diff_ref") or "diff/timeline-diff.json"
    operation["recovery_ref"] = operation.get("recovery_ref") or "recovery/recovery-map.json"


def _latest_decisions(session: dict[str, Any]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for decision in session.get("decisions", []):
        latest[str(decision.get("operation_id"))] = decision
    return latest


def replay_review_session(timeline: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(timeline)
    operations = {op.get("operation_id"): op for op in updated.get("operations", [])}
    for operation_id, decision in _latest_decisions(session).items():
        if operation_id not in operations:
            raise ValueError(f"operation {operation_id} was not found in timeline")
        op = operations[operation_id]
        action = decision.get("decision")
        provenance = op.setdefault("provenance", {})
        if action == "accept":
            op["state"] = "accepted"
            _attach_artifact_refs(op)
            provenance["manual_review"] = {
                "decision": "accepted",
                "reviewer": decision.get("reviewer", ""),
                "note": decision.get("note", ""),
                "reviewed_at": decision.get("decided_at", ""),
            }
        elif action == "reject":
            op["state"] = "rejected"
            provenance["manual_review"] = {
                "decision": "rejected",
                "reviewer": decision.get("reviewer", ""),
                "note": decision.get("note", ""),
                "reviewed_at": decision.get("decided_at", ""),
            }
        elif action == "undo":
            op["state"] = "proposed"
            provenance["undo"] = {
                "reviewer": decision.get("reviewer", ""),
                "reason": decision.get("note", ""),
                "undone_at": decision.get("decided_at", ""),
            }
            provenance.pop("manual_review", None)
    updated["recovery"] = build_recovery(updated)
    return updated


def review_status(session: dict[str, Any], total_operations: int | None = None) -> dict[str, Any]:
    latest = _latest_decisions(session)
    counts = {"accepted": 0, "rejected": 0, "undone": 0, "pending": None}
    for decision in latest.values():
        action = decision.get("decision")
        if action == "accept":
            counts["accepted"] += 1
        elif action == "reject":
            counts["rejected"] += 1
        elif action == "undo":
            counts["undone"] += 1
    if total_operations is not None:
        counts["pending"] = max(0, total_operations - len(latest))
    return {
        "schema_version": session.get("schema_version", SCHEMA_VERSION),
        "source_timeline": session.get("source_timeline"),
        "decision_event_count": len(session.get("decisions", [])),
        "decision_counts": counts,
        "latest_decisions": latest,
    }


def format_review_status_markdown(status: dict[str, Any]) -> str:
    counts = status.get("decision_counts", {})
    lines = [
        "# Review Session Status",
        "",
        f"Source timeline: {status.get('source_timeline')}",
        f"Decision events: {status.get('decision_event_count', 0)}",
        "",
        "## Counts",
        "",
        f"- Accepted: {counts.get('accepted', 0)}",
        f"- Rejected: {counts.get('rejected', 0)}",
        f"- Undone: {counts.get('undone', 0)}",
    ]
    if counts.get("pending") is not None:
        lines.append(f"- Pending: {counts.get('pending', 0)}")
    lines.extend([
        "",
        "## Latest decisions",
        "",
        "| Operation | Decision | Reviewer | Decided at |",
        "| --- | --- | --- | --- |",
    ])
    latest = status.get("latest_decisions", {})
    if latest:
        for operation_id, decision in sorted(latest.items()):
            lines.append(f"| {operation_id} | {decision.get('decision')} | {decision.get('reviewer')} | {decision.get('decided_at')} |")
    else:
        lines.append("| - | - | - | - |")
    return "\n".join(lines) + "\n"


def write_review_session(path: str | Path, session: dict[str, Any]) -> None:
    write_json(path, session)
