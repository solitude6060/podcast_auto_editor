# Review helper and local UI completion increment

## Goal
Complete the remaining interface roadmap items with a local-first review helper and a minimal localhost review UI that writes the same `review-session.json` state as the CLI.

## Scope
- UI-2: `review next` command that shows the next operation needing producer decision and the exact `review decide` command.
- UI-3: local single-user review server using Python stdlib only; it reads run artifacts and appends decisions to `review-session.json`.
- UI-4: desktop wrapper readiness via documented local URL command and generated shell launcher guidance; no packaged app yet because the local server must prove useful first.

## Acceptance criteria
- `podcast-auto-editor review next <session> --timeline <proposed>` returns the next undecided or undone operation with risk/confidence/preview/explanation fields.
- `review next` supports JSON and Markdown output.
- Local review server exposes GET status/next and POST decision handlers using existing `review_session.py` logic.
- Local server binds to localhost by default and rejects non-local host values unless explicitly overridden later.
- User-facing docs include Traditional Chinese coverage.
- Full uv pytest and compileall pass.
