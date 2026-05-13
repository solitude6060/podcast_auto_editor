# Review session state machine increment

## Goal
Start Phase A6 with a local, replayable review session file that can record producer decisions and rebuild an accepted timeline from the proposed timeline plus decisions.

## Acceptance criteria
- Review session JSON has schema/version, source timeline path, decisions, and summary counts.
- Decisions support `accept`, `reject`, and `undo` with reviewer, note, and timestamp metadata.
- Replaying a session onto a proposed timeline deterministically rebuilds operation states and recovery data.
- `podcast-auto-editor review status <session>` prints Markdown or JSON status.
- Tests cover replay, undo, persistence, status summaries, and CLI status output.

## Files
- `podcast_auto_editor/review_session.py`
- `podcast_auto_editor/cli.py`
- `tests/test_review_session.py`
- `tests/test_cli.py`
