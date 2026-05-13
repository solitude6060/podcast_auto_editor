import json

from podcast_auto_editor.review_session import apply_decision, create_review_session, format_review_status_markdown, replay_review_session, review_status, write_review_session
from podcast_auto_editor.timeline import create_noop_timeline, read_json


def _timeline():
    timeline = create_noop_timeline({"path": "input.wav", "duration": 6.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"] = [
        {"operation_id": "speech1", "type": "speech_cut", "source_range": {"start": 1.0, "end": 1.5}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "medium", "confidence": 0.8, "provenance": {"reason": "filler"}, "preview_ref": "preview/speech1.mp3", "diff_ref": None, "recovery_ref": None},
        {"operation_id": "silence1", "type": "silence_cut", "source_range": {"start": 3.0, "end": 4.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 1.0, "provenance": {}, "preview_ref": "preview/silence1.mp3", "diff_ref": None, "recovery_ref": None},
    ]
    return timeline


def test_review_session_replay_accept_reject_and_undo_decisions():
    session = create_review_session("timeline.proposed.v1.json")
    session = apply_decision(session, "speech1", "accept", reviewer="producer", note="remove filler", decided_at="2026-05-13T00:00:00Z")
    session = apply_decision(session, "silence1", "reject", reviewer="producer", note="keep dramatic pause", decided_at="2026-05-13T00:01:00Z")
    session = apply_decision(session, "silence1", "undo", reviewer="producer", note="defer", decided_at="2026-05-13T00:02:00Z")

    rebuilt = replay_review_session(_timeline(), session)

    states = {op["operation_id"]: op["state"] for op in rebuilt["operations"]}
    assert states == {"speech1": "accepted", "silence1": "proposed"}
    speech = next(op for op in rebuilt["operations"] if op["operation_id"] == "speech1")
    assert speech["provenance"]["manual_review"]["reviewer"] == "producer"
    assert rebuilt["recovery"]["removed_segments"][0]["operation_id"] == "speech1"


def test_review_status_summarizes_latest_decisions():
    session = create_review_session("timeline.json")
    session = apply_decision(session, "a", "accept", reviewer="p", decided_at="2026-05-13T00:00:00Z")
    session = apply_decision(session, "b", "reject", reviewer="p", decided_at="2026-05-13T00:01:00Z")
    session = apply_decision(session, "b", "undo", reviewer="p", decided_at="2026-05-13T00:02:00Z")

    status = review_status(session)

    assert status["decision_counts"] == {"accepted": 1, "rejected": 0, "undone": 1, "pending": None}
    assert status["latest_decisions"]["b"]["decision"] == "undo"


def test_review_session_persistence_roundtrip(tmp_path):
    path = tmp_path / "review-session.json"
    session = apply_decision(create_review_session("timeline.json"), "a", "accept", reviewer="p", decided_at="2026-05-13T00:00:00Z")

    write_review_session(path, session)

    assert read_json(path) == session
    assert json.loads(path.read_text())["schema_version"] == "review-session.v1"


def test_format_review_status_markdown():
    session = apply_decision(create_review_session("timeline.json"), "a", "accept", reviewer="p", decided_at="2026-05-13T00:00:00Z")

    markdown = format_review_status_markdown(review_status(session))

    assert "# Review Session Status" in markdown
    assert "- Accepted: 1" in markdown
    assert "| a | accept | p | 2026-05-13T00:00:00Z |" in markdown
