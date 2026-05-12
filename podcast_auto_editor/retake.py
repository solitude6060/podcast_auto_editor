from __future__ import annotations

import difflib
import re
from typing import Any

from .config import RetakeConfig
from .timeline import new_operation_id

_WORD_RE = re.compile(r"[\w']+", re.UNICODE)


def normalize_text(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(a=normalize_text(a), b=normalize_text(b)).ratio()


def _has_marker(text: str, config: RetakeConfig) -> str | None:
    lowered = text.lower()
    return next((marker for marker in config.marker_phrases if marker in lowered), None)


def detect_retake_candidates(transcript_segments: list[dict[str, Any]], config: RetakeConfig) -> list[dict[str, Any]]:
    """Detect conservative retake candidates from transcript segments."""
    candidates: list[dict[str, Any]] = []
    for idx, seg in enumerate(transcript_segments):
        text = str(seg.get("text", ""))
        marker = _has_marker(text, config)
        if marker and idx > 0:
            prev = transcript_segments[idx - 1]
            candidates.append(_candidate_from_segments(prev, seg, "explicit_marker", 0.93, marker))
            continue
        if idx == 0:
            continue
        prev = transcript_segments[idx - 1]
        distance = float(seg.get("start", 0)) - float(prev.get("end", prev.get("start", 0)))
        score = similarity(str(prev.get("text", "")), text)
        if 0 <= distance <= config.duplicate_window_s and score >= 0.88:
            candidates.append(_candidate_from_segments(prev, seg, "near_duplicate", min(0.95, score), None))
    return candidates


def _candidate_from_segments(remove_seg: dict[str, Any], evidence_seg: dict[str, Any], reason: str, confidence: float, marker: str | None) -> dict[str, Any]:
    return {
        "operation_id": new_operation_id("retake"),
        "type": "retake_cut",
        "source_range": {"start": float(remove_seg["start"]), "end": float(remove_seg["end"]), "unit": "seconds"},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "proposed",
        "risk": "low",
        "confidence": round(confidence, 4),
        "provenance": {
            "detector": "transcript.retake_heuristic",
            "reason": reason,
            "marker": marker,
            "remove_text": remove_seg.get("text", ""),
            "evidence_text": evidence_seg.get("text", ""),
        },
        "preview_ref": None,
        "diff_ref": None,
        "recovery_ref": None,
    }


def may_auto_accept_retake(operation: dict[str, Any], config: RetakeConfig, artifacts_exist: bool, non_overlap_evidence: bool = True) -> tuple[bool, str]:
    if operation.get("type") != "retake_cut":
        return False, "not a retake_cut"
    if not config.auto_low_risk_speech:
        return False, "auto_low_risk_speech disabled"
    if operation.get("risk") != "low":
        return False, "risk is not low"
    if float(operation.get("confidence", 0.0)) < config.auto_accept_confidence:
        return False, "confidence below threshold"
    if not non_overlap_evidence:
        return False, "missing non-overlap evidence"
    if not artifacts_exist:
        return False, "missing preview/diff/recovery artifacts"
    provenance = operation.get("provenance", {})
    if provenance.get("reason") not in {"explicit_marker", "near_duplicate", "transcript_supported_repeat"}:
        return False, "unsupported reason"
    forbidden = provenance.get("forbidden_reason")
    if forbidden:
        return False, f"forbidden: {forbidden}"
    return True, "accepted by low-risk retake policy"
