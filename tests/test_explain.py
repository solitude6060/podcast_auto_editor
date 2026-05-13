import pytest

from podcast_auto_editor.explain import explain_operation, format_explanation_markdown
from podcast_auto_editor.timeline import create_noop_timeline


def _timeline_with_operation(operation):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 5.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append(operation)
    return timeline


def test_explain_operation_extracts_speech_trust_fields():
    timeline = _timeline_with_operation({
        "operation_id": "retake1",
        "type": "retake_cut",
        "source_range": {"start": 1.0, "end": 2.0},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "proposed",
        "risk": "low",
        "confidence": 0.92,
        "provenance": {
            "detector": "transcript.retake_heuristic",
            "reason": "near_duplicate",
            "evidence_text": "I mean the corrected sentence",
            "auto_accept_policy": "manual review required until preview/diff/recovery exist",
            "operation_preview": {
                "before_after_ref": "preview/operations/retake1/before-after.mp3",
                "removed_ref": "preview/operations/retake1/removed.mp3",
            },
        },
        "preview_ref": "preview/operations/retake1/before-after.mp3",
        "diff_ref": "diff/timeline-diff.json",
        "recovery_ref": "recovery/recovery-map.json",
    })

    explanation = explain_operation(timeline, "retake1")

    assert explanation["operation_id"] == "retake1"
    assert explanation["detector"] == "transcript.retake_heuristic"
    assert explanation["reason_code"] == "near_duplicate"
    assert explanation["evidence_text"] == "I mean the corrected sentence"
    assert explanation["required_review"] == "manual_review_required"
    assert explanation["artifact_refs"] == {
        "preview": "preview/operations/retake1/before-after.mp3",
        "removed": "preview/operations/retake1/removed.mp3",
        "diff": "diff/timeline-diff.json",
        "recovery": "recovery/recovery-map.json",
    }


def test_explain_operation_marks_safe_deterministic_cut():
    timeline = _timeline_with_operation({
        "operation_id": "silence1",
        "type": "silence_cut",
        "source_range": {"start": 0.5, "end": 1.5},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "accepted",
        "risk": "deterministic",
        "confidence": 1.0,
        "provenance": {"detector": "ffmpeg.silencedetect", "reason": "long_silence"},
        "preview_ref": "preview/operations/silence1/before-after.mp3",
        "diff_ref": "diff/timeline-diff.json",
        "recovery_ref": "recovery/recovery-map.json",
    })

    explanation = explain_operation(timeline, "silence1")

    assert explanation["required_review"] == "safe_default_review_optional"
    assert explanation["evidence_text"] == ""


def test_explain_operation_rejects_unknown_id():
    timeline = _timeline_with_operation({
        "operation_id": "cut1",
        "type": "silence_cut",
        "source_range": {"start": 0.5, "end": 1.5},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "proposed",
        "risk": "deterministic",
        "confidence": 1.0,
        "provenance": {},
        "preview_ref": None,
        "diff_ref": None,
        "recovery_ref": None,
    })

    with pytest.raises(ValueError, match="operation missing was not found"):
        explain_operation(timeline, "missing")


def test_format_explanation_markdown_contains_trust_fields():
    explanation = {
        "operation_id": "speech1",
        "type": "speech_cut",
        "state": "proposed",
        "source": {"start": 1.0, "end": 1.4},
        "detector": "transcript.speech_cleanup_heuristic",
        "reason_code": "filler_phrase",
        "evidence_text": "um",
        "confidence": 0.8,
        "risk": "medium",
        "required_review": "manual_review_required",
        "artifact_refs": {"preview": "preview.mp3", "removed": None, "diff": None, "recovery": None},
    }

    markdown = format_explanation_markdown(explanation)

    assert "# Operation Explanation: speech1" in markdown
    assert "- Detector: transcript.speech_cleanup_heuristic" in markdown
    assert "- Required review: manual_review_required" in markdown
    assert "- Evidence: um" in markdown
