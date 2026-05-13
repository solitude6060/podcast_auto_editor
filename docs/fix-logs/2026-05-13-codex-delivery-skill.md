# Codex delivery skill and agent setup

## Source reference
Read local Claude Code guidance from `~/.claude/CLAUDE.md` and selected `~/.claude/skills/*/SKILL.md` files. Credential and telemetry files were not copied.

## Created
- Global Codex skill: `~/.codex/skills/strict-delivery-flow/SKILL.md`
- Global Codex reviewer agent: `~/.codex/agents/strict-delivery-reviewer.toml`
- Repository agent contract: `AGENTS.md`
- Interface roadmap: `docs/plans/2026-05-13-interface-roadmap.md`

## Key rules captured
- Spec before code.
- TDD before implementation.
- Plan in repository files, not chat.
- Review findings require verification and fix logs.
- Feature branches target `dev`; staged `dev` merges to `main` only after PR/code review and full verification.
- Interface progression: CLI contract → static HTML → text-mode review helper → local single-user UI → optional desktop wrapper.
- `.omx/`, `.venv/`, credentials, and generated artifacts remain local-only.
