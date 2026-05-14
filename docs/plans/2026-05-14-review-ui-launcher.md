# Local review UI launcher

## Goal
Complete the UI-4 desktop-wrapper-ready slice without adding desktop framework dependencies: generate local launcher files that start the localhost review UI for a run directory.

## Scope
- Add launcher generation helpers for POSIX shell scripts and optional Linux `.desktop` files.
- Add `review launcher <run_dir> --out <script> [--desktop-out <file>]` CLI command.
- Keep launcher host validation localhost-only.
- Keep generated files local artifacts; they are not committed run output.
- Document English and Traditional Chinese usage.

## Acceptance criteria
- Generated shell launcher starts `python -m podcast_auto_editor review serve <run_dir>` on a localhost host/port.
- Generated launcher quotes paths safely for spaces and shell metacharacters.
- Optional `.desktop` file points at the generated launcher and is marked non-terminal.
- Invalid host values are rejected before writing launcher files.
- Full uv pytest and compileall pass.
