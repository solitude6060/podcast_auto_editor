# Plan: Validate-run command

Date: 2026-05-15
Branch: `feature/validate-run-command`

## Goal

Add a `validate-run` CLI command that validates a config file, a timeline, and an optional transcript together before media processing. This closes the remaining validation-hardening gap from the roadmap by catching cross-file transcript duration errors before `run`, `dry-run`, or render work begins.

## Constraints

- Use existing validators instead of introducing a new schema dependency.
- Keep validation read-only; the command must not write run artifacts or media exports.
- Config validation must reuse `load_config` / `validate_config`.
- Timeline validation must reuse `validate_timeline`.
- Transcript validation must reuse `load_transcript_segments` and add duration-bound checks when a timeline media duration or explicit duration is available.
- Keep `.omx` untracked and use uv for verification.

## CLI contract

```bash
uv run python -m podcast_auto_editor validate-run \
  --config config.json \
  --timeline runs/episode/timeline.proposed.v1.json \
  --transcript-json transcript.json
```

Optional override:

```bash
uv run python -m podcast_auto_editor validate-run \
  --timeline timeline.json \
  --transcript-json transcript.json \
  --duration 3600
```

## Acceptance criteria

- Valid config + timeline + transcript exits 0 and prints a concise OK summary.
- Invalid config exits 1 with actionable config error text.
- Invalid timeline exits 1 with timeline validation errors.
- Transcript cues ending after the known media duration exit 1 before any artifact write.
- Command can validate only a config, only a timeline, only a transcript, or any combination.
- README and README.zh-TW document the preflight command.
