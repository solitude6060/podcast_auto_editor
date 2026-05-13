# AGENTS.md — Podcast Auto Editor

This repository follows a Claude-inspired but Codex-native delivery discipline.

## Operating rules

1. **Spec before code**
   - Read `README.md`, `docs/sdd/podcast-auto-editor-mvp.md`, and the relevant plan under `docs/plans/` before behavior changes.
   - If spec and code disagree, update the spec/plan or record a decision before changing implementation.

2. **TDD before implementation**
   - Behavior changes require a failing test first, then the smallest passing implementation.
   - Bug fixes require a regression test that reproduces the bug.
   - Docs-only changes may skip tests, but the commit body must say why.

3. **Plan with files**
   - Non-trivial work starts with `docs/plans/YYYY-MM-DD-<slug>.md`.
   - Completion evidence, review fixes, or phase logs go under `docs/fix-logs/` or `docs/reviews/`.
   - Do not rely on chat-only plans as the durable contract.

4. **Branch and PR flow**
   - Feature branches come from `dev`.
   - Feature completion: PR/code review into `dev`.
   - Phase completion: full verification on `dev`, then PR/code review from `dev` into `main`.
   - Do not commit feature work directly to `main`.
   - Hotfixes may branch from `main`, but still need review and full verification.

5. **Review handling**
   - Code review findings must be verified against current code before fixing.
   - Multi-finding reviews need a triage table: finding, severity, risk, this PR?, why.
   - Fixes follow TDD and get a matching fix log.

6. **Surgical changes**
   - Touch only what the task requires.
   - Avoid opportunistic refactors or formatting churn.
   - Remove only dead code introduced by the current change unless cleanup is the task.

7. **Verification gate**
   - Before claiming completion or merging:
     - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider`
     - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests`
     - Prefer `./scripts/smoke.sh` at PR/merge boundaries.
     - `git ls-files .omx` must be empty.
     - Recent commit messages must not contain `Co-authored-by` unless explicitly requested.

8. **Local-only hygiene**
   - Never track `.omx/`, `.venv/`, caches, credentials, telemetry, generated `runs/`, or local artifacts.
   - Do not copy secrets from `~/.claude`, `~/.codex`, or environment files into repo artifacts.

9. **Communication**
   - User-facing progress/final messages default to concise Traditional Chinese.
   - Use concrete evidence: commands, pass counts, commit hashes, branch names.
   - Repo docs, code, commits, and PR descriptions stay English.

10. **Interface planning**
   - Usability work follows `docs/plans/2026-05-13-interface-roadmap.md`.
   - Default progression: stable CLI contract → static HTML report → text-mode review helper → local single-user UI → optional desktop wrapper.
   - Do not add server/cloud collaboration or publishing upload unless explicitly requested.

## Codex skill and reviewer agent

Global Codex skill: `~/.codex/skills/strict-delivery-flow/SKILL.md`.
Global reviewer agent: `~/.codex/agents/strict-delivery-reviewer.toml`.

For non-trivial work, use `strict-delivery-flow` as the compact workflow checklist.
For merge readiness review, use `strict-delivery-reviewer` as the review lens.
