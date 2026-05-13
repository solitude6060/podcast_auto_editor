from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .review_session import apply_decision, next_review_item, review_status, write_review_session
from .timeline import read_json

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def validate_review_host(host: str) -> str:
    if host not in LOCAL_HOSTS:
        raise ValueError("review server binds to localhost only; use 127.0.0.1 or localhost")
    return host


def _paths(run_dir: str | Path) -> tuple[Path, Path]:
    root = Path(run_dir)
    return root / "timeline.proposed.v1.json", root / "review-session.json"


def load_review_context(run_dir: str | Path) -> dict[str, Any]:
    root = Path(run_dir)
    timeline_path, session_path = _paths(root)
    timeline = read_json(timeline_path)
    session = read_json(session_path) if session_path.exists() else {"schema_version": "review-session.v1", "source_timeline": str(timeline_path), "decisions": []}
    operations = timeline.get("operations", []) if isinstance(timeline.get("operations"), list) else []
    return {
        "run_dir": str(root),
        "timeline": str(timeline_path),
        "session": str(session_path),
        "status": review_status(session, total_operations=len(operations)),
        "next": next_review_item(timeline, session, session_path=str(session_path)),
    }


def handle_api_decision(run_dir: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    root = Path(run_dir)
    _, session_path = _paths(root)
    session = read_json(session_path) if session_path.exists() else {"schema_version": "review-session.v1", "source_timeline": str(_paths(root)[0]), "decisions": []}
    session = apply_decision(
        session,
        str(payload.get("operation_id") or ""),
        str(payload.get("decision") or ""),
        str(payload.get("reviewer") or ""),
        note=str(payload.get("note") or ""),
        decided_at=payload.get("decided_at"),
    )
    write_review_session(session_path, session)
    return load_review_context(root)


def build_review_app_html(run_dir: str | Path) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Podcast Auto Editor Review</title>
  <style>body {{ font-family: system-ui, sans-serif; margin: 2rem; }} button {{ margin-right: .5rem; }}</style>
</head>
<body>
  <h1>Podcast Auto Editor Review</h1>
  <p>Run directory: <code>{Path(run_dir)}</code></p>
  <p>State file: <code>review-session.json</code></p>
  <pre id=\"status\">Loading…</pre>
  <script>
    async function refresh() {{
      const status = await fetch('/api/status').then(r => r.json());
      document.getElementById('status').textContent = JSON.stringify(status, null, 2);
    }}
    async function decide(operation_id, decision, reviewer) {{
      await fetch('/api/decision', {{method: 'POST', headers: {{'content-type': 'application/json'}}, body: JSON.stringify({{operation_id, decision, reviewer}})}});
      await refresh();
    }}
    refresh();
  </script>
</body>
</html>
"""


class ReviewRequestHandler(BaseHTTPRequestHandler):
    run_dir: Path

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib hook name
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            body = build_review_app_html(self.run_dir).encode()
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/status":
            self._send_json(load_review_context(self.run_dir))
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib hook name
        if urlparse(self.path).path != "/api/decision":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode() or "{}")
            self._send_json(handle_api_decision(self.run_dir, payload))
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=400)


def serve_review_app(run_dir: str | Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    host = validate_review_host(host)

    class Handler(ReviewRequestHandler):
        pass

    Handler.run_dir = Path(run_dir)
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Review UI: http://{host}:{server.server_port}/")
    server.serve_forever()
