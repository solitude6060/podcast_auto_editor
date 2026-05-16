import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from podcast_auto_editor.local_review_server import (
    ReviewRequestHandler,
    build_review_app_html,
    handle_api_decision,
    load_review_context,
    validate_review_host,
)
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
    assert context["ai_draft"] is None
    assert context["status"]["decision_counts"]["pending"] == 1
    assert context["next"]["operation_id"] == "speech1"


def test_load_review_context_includes_ai_draft_relative_path(tmp_path):
    root = _run_dir(tmp_path)
    ai_dir = root / "ai"
    ai_dir.mkdir()
    (ai_dir / "ai-draft.v1.json").write_text("{}")

    context = load_review_context(root)

    assert context["ai_draft"] == "ai/ai-draft.v1.json"


def test_handle_api_decision_appends_to_review_session(tmp_path):
    root = _run_dir(tmp_path)

    payload = handle_api_decision(root, {"operation_id": "speech1", "decision": "accept", "reviewer": "producer", "note": "ok", "decided_at": "2026-05-13T00:00:00Z"})

    assert payload["status"]["decision_counts"]["accepted"] == 1
    session = json.loads((root / "review-session.json").read_text())
    assert session["decisions"][0]["operation_id"] == "speech1"


def test_build_review_app_html_is_static_and_local(tmp_path):
    root = _run_dir(tmp_path)

    html = build_review_app_html(root)

    assert "Run Dashboard" in html
    assert "AI Draft" in html
    assert "Podcast Auto Editor Review" in html
    assert "fetch('/api/status')" in html
    assert "/api/decision" in html
    assert "decideCurrent('accept')" in html
    assert "decideCurrent('reject')" in html
    assert "decideCurrent('undo')" in html
    assert "id=\"reviewer\"" in html
    assert "id=\"note\"" in html
    assert "review-session.json" in html


def test_build_review_app_html_escapes_run_dir():
    html = build_review_app_html('/tmp/run-<script>alert("x")</script>')

    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html
    assert "&quot;x&quot;" in html


def test_validate_review_host_defaults_to_localhost_only():
    assert validate_review_host("127.0.0.1") == "127.0.0.1"
    assert validate_review_host("localhost") == "localhost"
    with pytest.raises(ValueError, match="review server binds to localhost only"):
        validate_review_host("0.0.0.0")


def _spawn_review_server(tmp_path):
    root = _run_dir(tmp_path)
    (root / "ai").mkdir(exist_ok=True)
    (root / "ai" / "ai-draft.v1.json").write_text(json.dumps({"schema_version": "ai-draft.v1", "chapters": []}))

    class Handler(ReviewRequestHandler):
        pass

    Handler.run_dir = root
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, root


def _get(port: int, path: str) -> http.client.HTTPResponse:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path)
    response = conn.getresponse()
    response.read()
    return response


def test_dashboard_serves_allowlisted_artifact_files(tmp_path):
    """Regression for review: the dashboard renders <a href> links for
    timeline.proposed.v1.json, review-session.json, and ai/ai-draft.v1.json,
    but do_GET previously routed everything except /, /index.html, /api/status
    to 404 — so every artifact link in the UI was broken."""
    server, _root = _spawn_review_server(tmp_path)
    try:
        port = server.server_port
        for path in (
            "/timeline.proposed.v1.json",
            "/review-session.json",
            "/ai/ai-draft.v1.json",
        ):
            response = _get(port, path)
            assert response.status == 200, f"{path} -> {response.status}"
            assert response.getheader("content-type", "").startswith("application/json"), (
                f"{path} content-type: {response.getheader('content-type')!r}"
            )
    finally:
        server.shutdown()


def test_dashboard_rejects_paths_outside_allowlist(tmp_path):
    """Path-traversal guard: only the allowlisted artifact filenames are served."""
    server, _root = _spawn_review_server(tmp_path)
    try:
        port = server.server_port
        for bad in (
            "/secret.txt",
            "/../../../etc/passwd",
            "/ai/../etc/passwd",
            "/ai/unknown.json",
        ):
            response = _get(port, bad)
            assert response.status == 404, f"{bad} -> {response.status}"
    finally:
        server.shutdown()
