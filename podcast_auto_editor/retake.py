from __future__ import annotations

import difflib
import re
from typing import Any

from .config import RetakeConfig
from .timeline import new_operation_id

_WORD_RE = re.compile(r"[\w']+", re.UNICODE)
_FILLERS = {"um", "uh", "erm", "ah"}
# Short affirmative interjections. Per-speaker config can disable for hosts who
# rely on backchannel as part of their style.
_BACKCHANNELS = {"right", "okay", "mhm", "uh-huh", "yeah", "對", "對對", "對對對"}


def _speaker_skipped(speaker_id: str | None, speaker_aggression: dict[str, str] | None) -> bool:
    if not speaker_aggression or not speaker_id:
        return False
    return speaker_aggression.get(speaker_id) == "off"


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


def detect_speech_cleanup_candidates(
    transcript_segments: list[dict[str, Any]],
    speaker_aggression: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Detect conservative filler/false-start cleanup candidates.

    These are speech-changing edits, so they always remain proposed and require
    explicit manual review before render may remove them.

    `speaker_aggression` is an optional ``{speaker_id: level}`` map; speakers
    mapped to ``"off"`` are skipped (their fillers stay in). Cues without a
    ``speaker_id`` or with a speaker not in the map use the default behaviour.
    """
    candidates: list[dict[str, Any]] = []
    for seg in transcript_segments:
        speaker_id = seg.get("speaker_id")
        if _speaker_skipped(speaker_id if isinstance(speaker_id, str) else None, speaker_aggression):
            continue
        text = str(seg.get("text", ""))
        normalized = normalize_text(text)
        reason = None
        confidence = 0.0
        if normalized in _FILLERS:
            reason = "filler"
            confidence = 0.85
        elif text.rstrip().endswith(("--", "—", "-")):
            reason = "false_start"
            confidence = 0.80
        if reason:
            provenance: dict[str, Any] = {
                "detector": "transcript.speech_cleanup_heuristic",
                "reason": reason,
                "text": text,
                "auto_accept_policy": "manual review required for speech_cut",
            }
            if isinstance(speaker_id, str) and speaker_id:
                provenance["speaker_id"] = speaker_id
            candidates.append(
                {
                    "operation_id": new_operation_id("speech"),
                    "type": "speech_cut",
                    "source_range": {"start": float(seg["start"]), "end": float(seg["end"]), "unit": "seconds"},
                    "output_range": None,
                    "affected_tracks": ["audio:0"],
                    "state": "proposed",
                    "risk": "medium",
                    "confidence": confidence,
                    "provenance": provenance,
                    "preview_ref": None,
                    "diff_ref": None,
                    "recovery_ref": None,
                }
            )
    return candidates


def detect_backchannel_candidates(
    transcript_segments: list[dict[str, Any]],
    speaker_aggression: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Detect short affirmative interjections ("right", "mhm", "對對對") as
    a distinct ``backchannel_cut`` operation type. Speech-changing; always
    proposed-only; never auto-accepted by render.

    `speaker_aggression` accepts the same ``{speaker_id: level}`` shape as
    `detect_speech_cleanup_candidates`; speakers set to ``"off"`` are skipped.
    """
    candidates: list[dict[str, Any]] = []
    for seg in transcript_segments:
        speaker_id = seg.get("speaker_id")
        if _speaker_skipped(speaker_id if isinstance(speaker_id, str) else None, speaker_aggression):
            continue
        text = str(seg.get("text", ""))
        normalized = normalize_text(text)
        if normalized not in _BACKCHANNELS:
            continue
        provenance: dict[str, Any] = {
            "detector": "transcript.backchannel_heuristic",
            "reason": "backchannel",
            "text": text,
            "auto_accept_policy": "manual review required for backchannel_cut",
        }
        if isinstance(speaker_id, str) and speaker_id:
            provenance["speaker_id"] = speaker_id
        candidates.append(
            {
                "operation_id": new_operation_id("backchannel"),
                "type": "backchannel_cut",
                "source_range": {"start": float(seg["start"]), "end": float(seg["end"]), "unit": "seconds"},
                "output_range": None,
                "affected_tracks": ["audio:0"],
                "state": "proposed",
                "risk": "medium",
                "confidence": 0.80,
                "provenance": provenance,
                "preview_ref": None,
                "diff_ref": None,
                "recovery_ref": None,
            }
        )
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
