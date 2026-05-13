# HTML report review polish increment

## Goal
Continue the interface roadmap UI-1 by making the static HTML report more useful for producer review: summarize operations by risk/detector, surface review-session status when present, and visually flag manual-review-required speech edits.

## Acceptance criteria
- HTML report shows operation groups by risk and detector.
- If `review-session.json` exists in the run directory, HTML includes review counts and a local link to the session file.
- Operations that need manual review get a stable CSS class and visible label.
- HTML output remains static, local, escaped, and dependency-free.
- CLI behavior remains unchanged except richer HTML content.

## Verification
- Add failing tests in `tests/test_html_report.py`.
- Run targeted tests, full uv pytest, and compileall.
- Confirm `.omx/` remains untracked and no co-author trailers are introduced.
