import json

from podcast_auto_editor.review_session import create_review_session, apply_decision, next_review_item, format_next_review_markdown
from podcast_auto_editor.timeline import create_noop_timeline


def _timeline():
    timeline = create_noop_timeline({"path": "input.wav", "duration": 5.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"] = [
        {"operation_id": "speech1", "type": "speech_cut", "source_range": {"start": 1.0, "end": 1.5}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "medium", "confidence": 0.8, "provenance": {"detector": "transcript.speech_cleanup_heuristic", "reason": "filler", "evidence_text": "um"}, "preview_ref": "preview/speech1.mp3", "diff_ref": None, "recovery_ref": None},
        {"operation_id": "silence1", "type": "silence_cut", "source_range": {"start": 3.0, "end": 4.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 1.0, "provenance": {"detector": "ffmpeg.silencedetect"}, "preview_ref": "preview/silence1.mp3", "diff_ref": None, "recovery_ref": None},
    ]
    return timeline


def test_next_review_item_returns_first_undecided_operation():
    item = next_review_item(_timeline(), create_review_session("timeline.json"), session_path="runs/ep/review-session.json")

    assert item["operation_id"] == "speech1"
    assert item["risk"] == "medium"
    assert item["detector"] == "transcript.speech_cleanup_heuristic"
    assert item["evidence_text"] == "um"
    assert item["preview_ref"] == "preview/speech1.mp3"
    assert "--operation-id speech1" in item["decision_commands"]["accept"]


def test_next_review_item_skips_accepted_and_rejected_but_revisits_undone():
    session = create_review_session("timeline.json")
    session = apply_decision(session, "speech1", "accept", reviewer="p", decided_at="2026-05-13T00:00:00Z")
    session = apply_decision(session, "silence1", "reject", reviewer="p", decided_at="2026-05-13T00:01:00Z")
    assert next_review_item(_timeline(), session) is None

    session = apply_decision(session, "silence1", "undo", reviewer="p", decided_at="2026-05-13T00:02:00Z")
    item = next_review_item(_timeline(), session)
    assert item["operation_id"] == "silence1"


def test_format_next_review_markdown_includes_commands():
    item = next_review_item(_timeline(), create_review_session("timeline.json"), session_path="review-session.json")

    markdown = format_next_review_markdown(item)

    assert "# Next Review Operation" in markdown
    assert "speech1" in markdown
    assert "preview/speech1.mp3" in markdown
    assert "podcast-auto-editor review decide review-session.json --operation-id speech1 --decision accept" in markdown


def test_format_next_review_markdown_handles_empty_queue():
    assert "No pending review operations" in format_next_review_markdown(None)
