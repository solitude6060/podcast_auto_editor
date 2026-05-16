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


def _spawn_with_multi_op(tmp_path):
    """Spawn a server with a timeline containing multiple proposed op types so filter / detail tests have data to work with."""
    root = tmp_path / "runs" / "multi"
    root.mkdir(parents=True)
    timeline = create_noop_timeline({"path": "input.wav", "duration": 10.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].extend([
        {"operation_id": "speech1", "type": "speech_cut", "source_range": {"start": 0.5, "end": 0.75}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "medium", "confidence": 0.8, "provenance": {"detector": "transcript.speech_cleanup_heuristic"}, "preview_ref": "preview/speech1.mp3", "diff_ref": None, "recovery_ref": None},
        {"operation_id": "silence1", "type": "silence_cut", "source_range": {"start": 1.0, "end": 2.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 1.0, "provenance": {"detector": "ffmpeg.silencedetect"}, "preview_ref": None, "diff_ref": None, "recovery_ref": None},
        {"operation_id": "retake1", "type": "retake_cut", "source_range": {"start": 3.0, "end": 4.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "low", "confidence": 0.9, "provenance": {"detector": "retake.heuristic"}, "preview_ref": None, "diff_ref": None, "recovery_ref": None},
    ])
    write_json(root / "timeline.proposed.v1.json", timeline)
    write_json(root / "review-session.json", {"schema_version": "review-session.v1", "source_timeline": "timeline.proposed.v1.json", "decisions": []})

    class Handler(ReviewRequestHandler):
        pass

    Handler.run_dir = root
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, root


def test_dashboard_operation_endpoint_returns_payload_for_known_id(tmp_path):
    """PR-B: per-operation detail endpoint must return full op payload so the
    dashboard detail pane can show risk/confidence/preview without the user
    parsing raw JSON from /api/status."""
    server, _root = _spawn_with_multi_op(tmp_path)
    try:
        response = _get(server.server_port, "/api/operation/silence1")
        assert response.status == 200, response.status
    finally:
        server.shutdown()


def test_dashboard_operation_endpoint_returns_correct_payload_shape(tmp_path):
    """Detail payload uses the canonical shape from review_session.next_review_item.

    Carries operation_id, type, risk, confidence, source (not source_range), and
    the explain-resolved preview_ref. Post-PR-B fix-round this aligns with the
    /api/status `next` field so dashboard consumers can share render logic."""
    server, _root = _spawn_with_multi_op(tmp_path)
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/api/operation/speech1")
        response = conn.getresponse()
        body = response.read().decode()
        payload = json.loads(body)
        assert payload["operation_id"] == "speech1"
        assert payload["type"] == "speech_cut"
        assert payload["risk"] == "medium"
        assert payload["confidence"] == 0.8
        assert payload["source"] == {"start": 0.5, "end": 0.75}
    finally:
        server.shutdown()


def test_dashboard_operation_endpoint_404s_for_unknown_id(tmp_path):
    """Unknown id → 404, not 500."""
    server, _root = _spawn_with_multi_op(tmp_path)
    try:
        response = _get(server.server_port, "/api/operation/does_not_exist")
        assert response.status == 404, response.status
    finally:
        server.shutdown()


def test_dashboard_operation_endpoint_rejects_path_traversal(tmp_path):
    """URL paths with `..` or extra slashes in the id segment must 404, not
    accidentally match adjacent endpoints or escape into other route prefixes."""
    server, _root = _spawn_with_multi_op(tmp_path)
    try:
        port = server.server_port
        for bad in (
            "/api/operation/..",
            "/api/operation/../api/status",
            "/api/operation/speech1/extra",
        ):
            response = _get(port, bad)
            assert response.status == 404, f"{bad} -> {response.status}"
    finally:
        server.shutdown()


def test_dashboard_operation_endpoint_rejects_bare_empty_path(tmp_path):
    """Regression for PR-B triple review (MiniMax HIGH): the bare empty id
    `/api/operation/` (trailing slash with nothing) must 404 explicitly."""
    server, _root = _spawn_with_multi_op(tmp_path)
    try:
        response = _get(server.server_port, "/api/operation/")
        assert response.status == 404, response.status
    finally:
        server.shutdown()


def test_dashboard_operation_endpoint_rejects_encoded_traversal(tmp_path):
    """Regression for PR-B triple review (Codex MEDIUM): the path guard must
    reject percent-encoded traversal variants. Before the fix the guard ran
    on the raw URL slice, so `%2e%2e`, `%2Fetc%2Fpasswd`, `%00` passed the
    literal check and only 404'd because find_operation didn't recognise
    those encoded ids — a hardening gap. Decoded forms (containing `/`,
    `..`, or NUL) must be rejected explicitly."""
    server, _root = _spawn_with_multi_op(tmp_path)
    try:
        port = server.server_port
        for bad in (
            "/api/operation/%2e%2e",  # decoded -> ..
            "/api/operation/%2Fetc%2Fpasswd",  # decoded -> /etc/passwd
            "/api/operation/speech1%00",  # NUL byte
            "/api/operation/%2e",  # decoded -> .
        ):
            response = _get(port, bad)
            assert response.status == 404, f"{bad} -> {response.status}"
    finally:
        server.shutdown()


def test_dashboard_operation_endpoint_payload_matches_next_review_item_shape(tmp_path):
    """Regression for PR-B triple review (Gemini HIGH + MiniMax CRITICAL):
    /api/operation/<id> must return the canonical shape that the dashboard
    detail pane needs — including decision_commands, source (not source_range),
    detector, reason_code, evidence_text, required_review, removed_ref — so
    consumers don't have to special-case two payload shapes."""
    server, _root = _spawn_with_multi_op(tmp_path)
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/api/operation/speech1")
        response = conn.getresponse()
        payload = json.loads(response.read().decode())
        # Canonical fields (matching review_session.next_review_item)
        assert payload["operation_id"] == "speech1"
        assert payload["type"] == "speech_cut"
        assert "source" in payload, "missing canonical `source` field"
        assert payload["source"] == {"start": 0.5, "end": 0.75}
        assert "decision_commands" in payload, "missing decision_commands"
        assert payload["decision_commands"]["accept"].endswith("--decision accept --reviewer <name>")
        assert "detector" in payload, "missing detector field from explain_operation"
        assert "reason_code" in payload, "missing reason_code from explain_operation"
    finally:
        server.shutdown()


def test_dashboard_status_filter_param_narrows_next(tmp_path):
    """PR-B: `GET /api/status?filter=silence_cut` should make `next` only
    consider silence_cut operations. The aggregate counts stay accurate."""
    server, _root = _spawn_with_multi_op(tmp_path)
    try:
        response = _get(server.server_port, "/api/status?filter=silence_cut")
        assert response.status == 200
        # The detailed payload check happens in the next test
    finally:
        server.shutdown()


def test_dashboard_status_filter_returns_next_of_requested_type(tmp_path):
    """Filter=retake_cut → next['type'] == 'retake_cut'."""
    server, _root = _spawn_with_multi_op(tmp_path)
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/api/status?filter=retake_cut")
        response = conn.getresponse()
        payload = json.loads(response.read().decode())
        assert payload["next"]["type"] == "retake_cut"
        assert payload["next"]["operation_id"] == "retake1"
    finally:
        server.shutdown()


def test_dashboard_html_contains_keyboard_handlers(tmp_path):
    """PR-B: HTML must register keyboard listeners for j/k/a/r/u so a producer
    can complete a review pass without leaving the keyboard."""
    root = _run_dir(tmp_path)
    html = build_review_app_html(root)
    assert "addEventListener('keydown'" in html or "addEventListener(\"keydown\"" in html
    # Verify the documented key bindings are present
    for key in ("'a'", "'r'", "'u'", "'j'", "'k'"):
        assert key in html, f"expected key binding for {key} in HTML"


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
