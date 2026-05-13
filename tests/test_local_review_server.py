import json

import pytest

from podcast_auto_editor.local_review_server import build_review_app_html, handle_api_decision, load_review_context, validate_review_host
from podcast_auto_editor.timeline import create_noop_timeline, write_json


def _run_dir(tmp_path):
    root = tmp_path / "runs" / "ep1"
    root.mkdir(parents=True)
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "speech1", "type": "speech_cut", "source_range": {"start": 0.5, "end": 0.75}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "medium", "confidence": 0.8, "provenance": {"detector": "transcript.speech_cleanup_heuristic"}, "preview_ref": "preview/speech1.mp3", "diff_ref": None, "recovery_ref": None})
    write_json(root / "timeline.proposed.v1.json", timeline)
    write_json(root / "review-session.json", {"schema_version": "review-session.v1", "source_timeline": "timeline.proposed.v1.json", "decisions": []})
    return root


def test_load_review_context_reads_run_artifacts(tmp_path):
    root = _run_dir(tmp_path)

    context = load_review_context(root)

    assert context["run_dir"] == str(root)
    assert context["status"]["decision_counts"]["pending"] == 1
    assert context["next"]["operation_id"] == "speech1"


def test_handle_api_decision_appends_to_review_session(tmp_path):
    root = _run_dir(tmp_path)

    payload = handle_api_decision(root, {"operation_id": "speech1", "decision": "accept", "reviewer": "producer", "note": "ok", "decided_at": "2026-05-13T00:00:00Z"})

    assert payload["status"]["decision_counts"]["accepted"] == 1
    session = json.loads((root / "review-session.json").read_text())
    assert session["decisions"][0]["operation_id"] == "speech1"


def test_build_review_app_html_is_static_and_local(tmp_path):
    root = _run_dir(tmp_path)

    html = build_review_app_html(root)

    assert "Podcast Auto Editor Review" in html
    assert "fetch('/api/status')" in html
    assert "review-session.json" in html


def test_validate_review_host_defaults_to_localhost_only():
    assert validate_review_host("127.0.0.1") == "127.0.0.1"
    assert validate_review_host("localhost") == "localhost"
    with pytest.raises(ValueError, match="review server binds to localhost only"):
        validate_review_host("0.0.0.0")
