# Interface roadmap for podcast auto editor

## Goal
Make the podcast auto-editor easier to use after the CLI MVP by adding a staged local-first interface track that preserves review safety, reversible timelines, and no-cloud constraints.

## Principles
- Local-first: no cloud collaboration, no upload/publishing automation unless explicitly requested later.
- Review-first: every risky edit remains inspectable through operation previews, explanation data, diff, and recovery artifacts.
- CLI remains the stable automation contract; interfaces consume the same run artifacts instead of inventing a separate workflow.
- Static/offline surfaces come before interactive applications.

## Interface phases

### UI-1 — Static HTML report polish
Current baseline exists via `podcast-auto-editor html-report`.
Next improvements:
- Add filter sections for proposed/accepted/rejected operations.
- Add risk and detector group summaries.
- Add direct links to operation explanations and review-session status.
- Add CSS states for manual review required vs safe default.

Acceptance:
- HTML remains static and local.
- Links stay relative to the run directory.
- Tests cover escaping and local artifact links.

### UI-2 — Text-mode review session helper
Add a terminal-friendly review workflow on top of review sessions.
Possible command shape:

```bash
podcast-auto-editor review next runs/ep1/review-session.json --timeline runs/ep1/timeline.proposed.v1.json
podcast-auto-editor review decide ...
podcast-auto-editor review rebuild ...
```

Acceptance:
- No interactive dependency required for scripted use.
- Output always names operation id, risk, confidence, preview refs, explanation fields, and next decision command.

### UI-3 — Local single-user web interface
Build a local-only UI that reads a run directory and writes review-session JSON.
Recommended architecture:
- Backend: stdlib `http.server` or tiny local adapter only if justified later.
- Frontend: static HTML/JS reading JSON artifacts.
- State: `review-session.json` and rebuilt timeline files only.

Acceptance:
- Runs only on localhost.
- No accounts, cloud sync, or publishing integration.
- Can operate on existing run directories.
- Uses same `review_session.py` replay logic.

### UI-4 — Optional desktop wrapper
Only if the local web UI is useful enough:
- Package the local UI as a desktop shortcut/wrapper.
- Keep CLI and artifact formats authoritative.

## Dependencies
- Current A2 preview refs and A4 explainability data.
- Current A6 review-session state machine.
- Current A7 static HTML report.

## Verification
- Unit tests for artifact parsing and HTML/JSON generation.
- End-to-end fixture using generated run artifacts.
- Security checks for HTML escaping and path traversal prevention.
