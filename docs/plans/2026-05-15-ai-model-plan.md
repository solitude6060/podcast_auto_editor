# Plan: AI model catalog and pull plan

Date: 2026-05-15
Branch: `feature/ai-model-plan`

## Goal

Add a local AI model catalog and `ai models` CLI so users can inspect safe model tiers and generate explicit Ollama pull commands without automatically downloading large models or consuming GPU resources.

## Constraints

- No automatic model downloads in tests, CI, or default CLI output.
- Model download commands are generated as text unless the user later runs them manually.
- Support a `smoke` tier for low-resource validation while another project may be using GPU.
- Mark 30B-class models as heavy/manual and not safe for concurrent GPU use.
- Keep MiniMax documented as non-local fallback only.
- Use only Python standard library.
- User-facing docs require Traditional Chinese coverage.

## CLI contract

```bash
uv run python -m podcast_auto_editor ai models --format markdown
uv run python -m podcast_auto_editor ai models --tier smoke --format json
uv run python -m podcast_auto_editor ai models --pull-plan --tier recommended
```

## Acceptance criteria

- Catalog includes smoke, recommended, and heavy/manual tiers.
- JSON output is scriptable and contains pull command strings.
- Markdown output warns about GPU sharing and manual download windows.
- Pull plan output never executes `ollama pull`.
- Tests verify no shell execution is performed by the planner.
