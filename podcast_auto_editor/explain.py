from __future__ import annotations

from typing import Any

SPEECH_CHANGING_TYPES = {"retake_cut", "speech_cut"}
DETERMINISTIC_SAFE_TYPES = {"silence_cut"}


def _find_operation(timeline: dict[str, Any], operation_id: str) -> dict[str, Any]:
    for op in timeline.get("operations", []):
        if op.get("operation_id") == operation_id:
            return op
    raise ValueError(f"operation {operation_id} was not found")


def _operation_preview_refs(operation: dict[str, Any]) -> tuple[str | None, str | None]:
    operation_preview = operation.get("provenance", {}).get("operation_preview", {})
    preview_ref = operation_preview.get("before_after_ref") or operation.get("preview_ref")
    removed_ref = operation_preview.get("removed_ref")
    return preview_ref, removed_ref


def _required_review(operation: dict[str, Any]) -> str:
    if operation.get("type") in SPEECH_CHANGING_TYPES:
        manual_review = operation.get("provenance", {}).get("manual_review")
        auto_policy = operation.get("provenance", {}).get("auto_accept_policy")
        if isinstance(manual_review, dict) and manual_review.get("decision") == "accepted":
            return "manual_review_complete"
        if isinstance(auto_policy, dict) and auto_policy.get("accepted") is True:
            return "auto_low_risk_review_complete"
        return "manual_review_required"
    if operation.get("type") in DETERMINISTIC_SAFE_TYPES and operation.get("risk") == "deterministic":
        return "safe_default_review_optional"
    return "review_recommended"


def explain_operation(timeline: dict[str, Any], operation_id: str) -> dict[str, Any]:
    operation = _find_operation(timeline, operation_id)
    provenance = operation.get("provenance", {})
    source = operation.get("source_range") or {}
    preview_ref, removed_ref = _operation_preview_refs(operation)
    return {
        "operation_id": operation.get("operation_id"),
        "type": operation.get("type"),
        "state": operation.get("state"),
        "source": {
            "start": float(source["start"]) if "start" in source else None,
            "end": float(source["end"]) if "end" in source else None,
        },
        "detector": provenance.get("detector") or "unknown",
        "reason_code": provenance.get("reason") or provenance.get("reason_code") or "unspecified",
        "evidence_text": provenance.get("evidence_text") or "",
        "confidence": operation.get("confidence"),
        "risk": operation.get("risk"),
        "required_review": _required_review(operation),
        "artifact_refs": {
            "preview": preview_ref,
            "removed": removed_ref,
            "diff": operation.get("diff_ref"),
            "recovery": operation.get("recovery_ref"),
        },
    }


def _format_source(source: dict[str, Any]) -> str:
    start = source.get("start")
    end = source.get("end")
    if start is None or end is None:
        return "-"
    return f"{float(start):.3f}-{float(end):.3f}"


def _format_confidence(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def format_explanation_markdown(explanation: dict[str, Any]) -> str:
    artifact_refs = explanation.get("artifact_refs") or {}
    lines = [
        f"# Operation Explanation: {explanation.get('operation_id')}",
        "",
        f"- Type: {explanation.get('type') or '-'}",
        f"- State: {explanation.get('state') or '-'}",
        f"- Source: {_format_source(explanation.get('source') or {})}",
        f"- Detector: {explanation.get('detector') or 'unknown'}",
        f"- Reason code: {explanation.get('reason_code') or 'unspecified'}",
        f"- Confidence: {_format_confidence(explanation.get('confidence'))}",
        f"- Risk: {explanation.get('risk') or '-'}",
        f"- Required review: {explanation.get('required_review') or '-'}",
        f"- Evidence: {explanation.get('evidence_text') or ''}",
        "",
        "## Artifacts",
        "",
        f"- Preview: {artifact_refs.get('preview') or '-'}",
        f"- Removed: {artifact_refs.get('removed') or '-'}",
        f"- Diff: {artifact_refs.get('diff') or '-'}",
        f"- Recovery: {artifact_refs.get('recovery') or '-'}",
    ]
    ai_explanation = explanation.get("ai_explanation") or {}
    if ai_explanation:
        lines.extend(
            [
                "",
                "## AI Explanation",
                f"- Dry prompt: {ai_explanation.get('dry_prompt', False)}",
                f"- Risk: {ai_explanation.get('risk') or ai_explanation.get('source', {}).get('risk') or '-'}",
                f"- Rationale: {ai_explanation.get('rationale') or ai_explanation.get('rationale_score') or ai_explanation.get('source', {}).get('rationale_score') or ''}",
                f"- Reason: {ai_explanation.get('rationale') or ai_explanation.get('llm_reason') or '-'}",
            ]
        )
    return "\n".join(lines) + "\n"
