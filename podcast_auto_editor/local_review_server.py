from __future__ import annotations

import html
import json
import shlex
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .explain import explain_operation
from .review_session import apply_decision, next_review_item, review_status, write_review_session
from .timeline import read_json

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
ARTIFACT_ALLOWLIST: tuple[str, ...] = (
    "timeline.proposed.v1.json",
    "review-session.json",
    "ai/ai-draft.v1.json",
)


def validate_review_host(host: str) -> str:
    if host not in LOCAL_HOSTS:
        raise ValueError("review server binds to localhost only; use 127.0.0.1 or localhost")
    return host


def _resolve_artifact_request(run_dir: Path, request_path: str) -> Path | None:
    """Return the on-disk path for an allowlisted artifact, or None.

    Only filenames in ARTIFACT_ALLOWLIST are served, and the resolved path
    must stay inside run_dir to prevent path traversal.
    """
    relative = request_path.lstrip("/")
    if relative not in ARTIFACT_ALLOWLIST:
        return None
    run_root = run_dir.resolve()
    candidate = (run_root / relative).resolve()
    try:
        candidate.relative_to(run_root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def _paths(run_dir: str | Path) -> tuple[Path, Path, Path]:
    root = Path(run_dir)
    return root / "timeline.proposed.v1.json", root / "review-session.json", root / "ai/ai-draft.v1.json"


def _relative_path(root: Path, value: str | Path | None) -> str | None:
    if not value:
        return None
    try:
        return Path(value).resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return str(value).replace("\\", "/")


def load_review_context(run_dir: str | Path, *, filter_type: str | None = None) -> dict[str, Any]:
    root = Path(run_dir)
    timeline_path, session_path, ai_draft_path = _paths(root)
    timeline = read_json(timeline_path)
    session = read_json(session_path) if session_path.exists() else {"schema_version": "review-session.v1", "source_timeline": str(timeline_path), "decisions": []}
    operations = timeline.get("operations", []) if isinstance(timeline.get("operations"), list) else []
    ai_draft = _relative_path(root, ai_draft_path) if ai_draft_path.exists() else None
    if filter_type:
        filtered_ops = [op for op in operations if op.get("type") == filter_type]
        timeline_for_next = {**timeline, "operations": filtered_ops}
    else:
        timeline_for_next = timeline
    return {
        "run_dir": str(root),
        "timeline": str(timeline_path),
        "session": str(session_path),
        "ai_draft": ai_draft,
        "filter": filter_type,
        "status": review_status(session, total_operations=len(operations)),
        "next": next_review_item(timeline_for_next, session, session_path=str(session_path)),
    }


def find_operation(run_dir: str | Path, operation_id: str) -> dict[str, Any] | None:
    """Return the canonical per-operation payload for ``operation_id``, or None.

    The shape mirrors ``review_session.next_review_item`` so the dashboard's
    detail pane and the `/api/status`-driven `next` pane can share rendering
    logic. Fields: operation_id, type, state, risk, confidence, source,
    detector, reason_code, evidence_text, required_review, preview_ref,
    removed_ref, decision_commands.
    """
    root = Path(run_dir)
    timeline_path, session_path, _ = _paths(root)
    if not timeline_path.exists():
        return None
    timeline = read_json(timeline_path)
    operations = timeline.get("operations", []) if isinstance(timeline.get("operations"), list) else []
    for op in operations:
        if str(op.get("operation_id")) != operation_id:
            continue
        explanation = explain_operation(timeline, operation_id)
        artifact_refs = explanation.get("artifact_refs", {}) if isinstance(explanation.get("artifact_refs"), dict) else {}
        return {
            "operation_id": operation_id,
            "type": op.get("type"),
            "state": op.get("state"),
            "risk": op.get("risk"),
            "confidence": op.get("confidence"),
            "source": op.get("source_range"),
            "detector": explanation.get("detector"),
            "reason_code": explanation.get("reason_code"),
            "evidence_text": explanation.get("evidence_text"),
            "required_review": explanation.get("required_review"),
            "preview_ref": artifact_refs.get("preview"),
            "removed_ref": artifact_refs.get("removed"),
            "decision_commands": {
                "accept": f"podcast-auto-editor review decide {session_path} --operation-id {operation_id} --decision accept --reviewer <name>",
                "reject": f"podcast-auto-editor review decide {session_path} --operation-id {operation_id} --decision reject --reviewer <name>",
                "undo": f"podcast-auto-editor review decide {session_path} --operation-id {operation_id} --decision undo --reviewer <name>",
            },
        }
    return None


def handle_api_decision(run_dir: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    root = Path(run_dir)
    _, session_path, _ = _paths(root)
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


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_review_app_html(run_dir: str | Path) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Podcast Auto Editor Review</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 72rem; }}
    button {{ margin-right: .5rem; }}
    label {{ display: block; margin: .5rem 0; }}
    input {{ min-width: 18rem; }}
    section {{ border: 1px solid #ddd; border-radius: .5rem; padding: 1rem; margin: 1rem 0; }}
    .muted {{ color: #555; }}
    pre {{ background: #f6f8fa; overflow: auto; padding: 1rem; }}
  </style>
</head>
<body>
  <h1>Podcast Auto Editor Review</h1>
  <section>
    <h2>Run Dashboard</h2>
    <p>Run directory: <code>{_escape(Path(run_dir))}</code></p>
    <p>State file: <code>review-session.json</code></p>
    <p>AI Draft: <span id=\"ai-draft\" class=\"muted\">Loading…</span></p>
  </section>
  <section>
    <h2>Next</h2>
    <div id=\"next\">Loading next operation…</div>
    <label>Reviewer <input id=\"reviewer\" value=\"local-reviewer\" autocomplete=\"name\"></label>
    <label>Note <input id=\"note\" placeholder=\"Optional decision note\"></label>
    <button id=\"accept\" type=\"button\" onclick=\"decideCurrent('accept')\">Accept</button>
    <button id=\"reject\" type=\"button\" onclick=\"decideCurrent('reject')\">Reject</button>
    <button id=\"undo\" type=\"button\" onclick=\"decideCurrent('undo')\">Undo</button>
  </section>
  <section>
    <h2>Artifacts</h2>
    <ul id=\"artifact-list\">
      <li><a href=\"timeline.proposed.v1.json\">timeline.proposed.v1.json</a></li>
      <li><a href=\"review-session.json\">review-session.json</a></li>
      <li id=\"artifact-ai-draft\"></li>
    </ul>
  </section>
  <section>
    <h2>Status</h2>
    <pre id=\"status\">Loading…</pre>
  </section>
  <script>
    let currentOperation = null;

    function renderNext(status) {{
      currentOperation = status.next;
      const target = document.getElementById('next');
      if (!currentOperation) {{
        target.textContent = 'No pending operations. Review is complete.';
        return;
      }}
      const summary = [
        `Operation: ${{currentOperation.operation_id}}`,
        `Type: ${{currentOperation.type}}`,
        `Risk: ${{currentOperation.risk || 'unknown'}}`,
        `Confidence: ${{currentOperation.confidence ?? 'unknown'}}`,
        `Reason: ${{currentOperation.reason || 'No reason provided'}}`,
        `Preview: ${{currentOperation.preview_ref || 'none'}}`
      ].join('\\n');
      target.textContent = summary;
    }}

    function setAiDraft(status) {{
      const aiDraft = document.getElementById('ai-draft');
      const artifactItem = document.getElementById('artifact-ai-draft');
      if (status.ai_draft) {{
        const link = document.createElement('a');
        link.href = status.ai_draft;
        link.textContent = status.ai_draft;
        aiDraft.textContent = '';
        aiDraft.appendChild(link);

        artifactItem.textContent = '';
        const itemLink = document.createElement('a');
        itemLink.href = status.ai_draft;
        itemLink.textContent = status.ai_draft;
        artifactItem.appendChild(itemLink);
        return;
      }}
      aiDraft.textContent = 'Not generated yet';
      artifactItem.textContent = 'AI draft missing';
    }}

    async function refresh() {{
      const status = await fetch('/api/status').then(r => r.json());
      document.getElementById('status').textContent = JSON.stringify(status, null, 2);
      renderNext(status);
      setAiDraft(status);
    }}

    async function decide(operation_id, decision, reviewer, note) {{
      await fetch('/api/decision', {{method: 'POST', headers: {{'content-type': 'application/json'}}, body: JSON.stringify({{operation_id, decision, reviewer, note}})}});
      await refresh();
    }}

    async function decideCurrent(decision) {{
      if (!currentOperation) {{
        return;
      }}
      await decide(
        currentOperation.operation_id,
        decision,
        document.getElementById('reviewer').value,
        document.getElementById('note').value
      );
      document.getElementById('note').value = '';
    }}

    document.addEventListener('keydown', (event) => {{
      const tag = event.target.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      if (event.key === 'a') decideCurrent('accept');
      else if (event.key === 'r') decideCurrent('reject');
      else if (event.key === 'u') decideCurrent('undo');
      // j and k both advance to the next pending operation. Real prev
      // navigation is reserved for a follow-up PR — kept consistent so muscle
      // memory does not accidentally regress a decision.
      else if (event.key === 'j') refresh();
      else if (event.key === 'k') refresh();
    }});

    refresh();
  </script>
</body>
</html>
"""


def build_launcher_script(run_dir: str | Path, host: str = "127.0.0.1", port: int = 8765) -> str:
    host = validate_review_host(host)
    return "\n".join(
        [
            "#!/usr/bin/env sh",
            "set -eu",
            f"exec python -m podcast_auto_editor review serve {shlex.quote(str(run_dir))} --host {shlex.quote(host)} --port {int(port)}",
            "",
        ]
    )


def _desktop_value(value: object) -> str:
    return str(value).replace("\n", " ").replace("\r", " ")


def build_linux_desktop_entry(script_path: str | Path, name: str = "Podcast Auto Editor Review") -> str:
    return "\n".join(
        [
            "[Desktop Entry]",
            "Type=Application",
            f"Name={_desktop_value(name)}",
            f"Exec={_desktop_value(script_path)}",
            "Terminal=false",
            "Categories=AudioVideo;",
            "",
        ]
    )


def write_review_launcher(
    run_dir: str | Path,
    out: str | Path,
    *,
    desktop_out: str | Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    name: str = "Podcast Auto Editor Review",
) -> dict[str, Path | None]:
    script = build_launcher_script(run_dir, host=host, port=port)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(script, encoding="utf-8")
    out_path.chmod(out_path.stat().st_mode | 0o755)
    desktop_path = Path(desktop_out) if desktop_out else None
    if desktop_path:
        desktop_path.parent.mkdir(parents=True, exist_ok=True)
        desktop_path.write_text(build_linux_desktop_entry(out_path, name=name), encoding="utf-8")
    return {"script": out_path, "desktop": desktop_path}


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
        parsed = urlparse(self.path)
        path = parsed.path
        if path in {"/", "/index.html"}:
            body = build_review_app_html(self.run_dir).encode()
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/status":
            params = parse_qs(parsed.query)
            filter_values = params.get("filter") or []
            filter_type = filter_values[0] if filter_values else None
            self._send_json(load_review_context(self.run_dir, filter_type=filter_type))
            return
        if path.startswith("/api/operation/"):
            raw_id = path[len("/api/operation/"):]
            # Decode percent-encoded variants (e.g. %2e%2e, %2F) before checking
            # the deny list so encoded traversal cannot bypass the guard.
            operation_id = unquote(raw_id)
            if (
                not operation_id
                or "/" in operation_id
                or "\\" in operation_id
                or operation_id in {".", ".."}
                or any(ord(ch) < 0x20 for ch in operation_id)
            ):
                self.send_error(404)
                return
            op = find_operation(self.run_dir, operation_id)
            if op is None:
                self.send_error(404)
                return
            self._send_json(op)
            return
        artifact = _resolve_artifact_request(self.run_dir, path)
        if artifact is not None:
            body = artifact.read_bytes()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
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
