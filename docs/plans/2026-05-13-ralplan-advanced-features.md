# RALPLAN-DR: Advanced Feature Roadmap for Podcast Auto Editor

## Scope
Plan post-MVP advanced features after the local-first MVP baseline is complete. This is not a rewrite plan; it extends the existing CLI/timeline/recovery architecture while preserving safety and reversibility.

## Current baseline
- MVP is complete and pushed through `4779497 Add local smoke verification path`.
- Core CLI supports `run`, `dry-run`, `report`, `review-accept`, `undo`, `validate-transcript`, `demo-fixtures`.
- Timeline/recovery/diff/preview/transcript/subtitle/chapter/quality/video-sync workflows are test-backed.
- Verification baseline: latest full suite reported 65 passing tests plus compileall.
- Constraints: uv-managed environment, local-first/no cloud by default, `.omx/` local-only, no `Co-authored-by` trailers.

## RALPLAN-DR summary

### Principles
1. Keep the timeline as the canonical source of truth before media mutation.
2. Treat every speech-changing edit as proposed until review or a stricter policy exists.
3. Add advanced capability behind inspectable artifacts, not opaque automation.
4. Prefer optional adapters over mandatory new dependencies.
5. Preserve fresh-clone local verification with uv and smoke tests.

### Decision drivers
1. Producer trust: explain why edits are proposed and make reversal obvious.
2. Output quality: keep publishable audio/video gates authoritative.
3. Extensibility: advanced AI/ASR/UI features must plug into stable CLI contracts.

### Viable options considered
- **Option A — Local-first advanced CLI platform (chosen).** Add plugin-like adapters, richer previews, batch/project workflows, and optional local ASR integrations. Pros: preserves current architecture and testability. Cons: less flashy than a GUI-first rewrite.
- **Option B — AI-first auto-editor.** Prioritize ASR/LLM automation and auto-cuts. Pros: faster perceived magic. Cons: higher false-positive risk and conflicts with low-risk automation requirement.
- **Option C — GUI-first product.** Build web/TUI around current commands. Pros: easier for producers. Cons: UI churn before advanced contracts are stable.

## ADR

### Decision
Adopt Option A: evolve the MVP into a local-first advanced CLI platform with optional adapters, richer artifacts, and later UI on top of stable commands.

### Drivers
- The current safety model is CLI/timeline based and works.
- User requirements prioritize publishable quality and low-risk automation.
- Optional adapters let the project grow without forcing cloud/API dependencies.

### Alternatives considered
- Full AI automation now: rejected until explainability and review loops are stronger.
- GUI now: deferred until batch/project/report contracts stabilize.
- Heavy dependency stack now: rejected unless isolated behind optional extras.

### Consequences
- Advanced work proceeds in bounded phases.
- Optional dependencies may be introduced only as explicit extras/adapters.
- CLI and artifact schemas remain the stability layer for future UI.

## Advanced phases

### Phase A1 — Project/batch workflow
**Goal:** Support multi-episode local processing without cloud collaboration.

Actions:
1. Add `project init` command that creates a local project manifest outside `.omx`.
2. Add `batch dry-run` over multiple media files.
3. Add aggregate report with per-episode status, warnings, duration removed, quality state.
4. Keep publishing/upload out of scope.

Acceptance:
- Batch dry-run never writes edited media exports.
- Failed episodes do not stop unrelated episodes unless `--fail-fast` is set.
- Aggregate report is JSON and Markdown.

Suggested files:
- `podcast_auto_editor/project.py`
- `podcast_auto_editor/cli.py`
- `tests/test_project_batch.py`

### Phase A2 — Per-operation preview pack
**Goal:** Make human review faster and safer.

Actions:
1. Generate per-operation before/after preview clips with configurable context padding.
2. Generate per-operation removed audio clips.
3. Link each operation to its own preview refs in the timeline.
4. Add `review-list` command that prints operation table with preview paths.

Acceptance:
- Every proposed/accepted operation can point to stable review artifacts.
- Missing FFmpeg remains a clear, gated failure.

Suggested files:
- `podcast_auto_editor/preview.py`
- `podcast_auto_editor/pipeline.py`
- `tests/test_preview_pack.py`

### Phase A3 — Optional local ASR adapter
**Goal:** Allow transcript generation without cloud dependency.

Actions:
1. Define transcript provider protocol returning `transcript.v1` segments.
2. Add `transcribe` command with provider selection.
3. Implement a `stub` provider first for deterministic tests.
4. Add optional local provider placeholder behind extras/config, not mandatory dependency.

Acceptance:
- Core tests pass without ASR dependencies.
- Provider output is validated by existing transcript validation.
- ASR failure never mutates media.

Suggested files:
- `podcast_auto_editor/asr.py`
- `tests/test_asr.py`
- `pyproject.toml` optional dependency groups only when provider is chosen.

### Phase A4 — Rich edit explainability
**Goal:** Improve producer trust for AI/speech proposals.

Actions:
1. Add evidence snippets around transcript-supported operations.
2. Add per-operation confidence/risk reason codes.
3. Add `explain` command for a timeline operation.
4. Add report section grouping operations by risk and detector.

Acceptance:
- Every speech-changing operation explains detector, evidence text, confidence, risk, and required review path.
- Reports can be generated without media files.

Suggested files:
- `podcast_auto_editor/explain.py`
- `tests/test_explain.py`

### Phase A5 — Export matrix and mastering profiles
**Goal:** Support publishable output variants.

Actions:
1. Add explicit export profiles: `podcast-stereo`, `podcast-mono`, `archive-wav`.
2. Generate WAV/MP3 outputs based on profile.
3. Run quality gates per export and report failures by profile.
4. Keep default profile backward compatible.

Acceptance:
- Failed export profile blocks success unless diagnostic mode is requested.
- Profile metadata is persisted in timeline/report.

Suggested files:
- `podcast_auto_editor/export_profiles.py`
- `podcast_auto_editor/media.py`
- `tests/test_export_profiles.py`

### Phase A6 — Review session state machine
**Goal:** Make producer review repeatable and resumable.

Actions:
1. Add local review session JSON under run directory.
2. Support accept/reject/undo decisions with reviewer identity and timestamps.
3. Add `review status` command.
4. Ensure session can regenerate accepted timeline from decisions.

Acceptance:
- Review decisions are replayable.
- Timeline can be rebuilt from source proposed timeline + review session.

Suggested files:
- `podcast_auto_editor/review_session.py`
- `tests/test_review_session.py`

### Phase A7 — Lightweight TUI or static HTML report
**Goal:** Improve usability without a full web app.

Actions:
1. Add static HTML report generated from existing run artifacts.
2. Optionally add text-mode review table first.
3. Do not add server/cloud collaboration.

Acceptance:
- HTML report is static and local.
- Links point to local preview/diff/recovery artifacts.

Suggested files:
- `podcast_auto_editor/html_report.py`
- `tests/test_html_report.py`

### Phase A8 — CI and release hygiene
**Goal:** Make public repo development safer.

Actions:
1. Add GitHub Actions only if desired for repository checks.
2. Run `uv run --group dev pytest` and compileall in CI.
3. Add release notes template and changelog.
4. Keep `.omx/` ignored.

Acceptance:
- CI mirrors local smoke script.
- No secrets/cloud credentials required.

## Execution sequence
Recommended order:
1. A2 per-operation preview pack — highest producer-safety value.
2. A4 explainability — improves safe review of AI proposals.
3. A6 review session state — makes decisions replayable.
4. A5 export profiles — improves publishing quality.
5. A1 batch workflow — useful once single-episode workflow is stable.
6. A3 optional ASR — larger dependency boundary; do after contracts stabilize.
7. A7 static HTML report — UI on stable artifacts.
8. A8 CI/release hygiene — add when repository process needs it.

## Available-agent-types roster
- `planner`: phase decomposition and acceptance criteria.
- `architect`: adapter boundaries, timeline schema, artifact contracts.
- `executor`: code implementation.
- `test-engineer`: regression/fixture strategy.
- `verifier`: final evidence and `.omx`/git hygiene audit.
- `code-reviewer`: safety and maintainability review.
- `writer`: README/SDD/fix-log updates.
- `dependency-expert`: optional ASR/export dependency evaluation.
- `designer`: static HTML/TUI report UX.

## Ralph launch hint
Use Ralph for one advanced phase at a time:

```bash
omx ralph "Execute docs/plans/2026-05-13-ralplan-advanced-features.md Phase A2 only. Follow strict SDD/TDD, uv verification, Lore commits, no .omx push, no Co-authored-by trailers."
```

## Team launch hint
Use team when a phase has independent implementation/test/docs lanes:

```bash
OMX_TEAM_WORKER_CLI=codex omx team 4:executor "
Use docs/plans/2026-05-13-ralplan-advanced-features.md as source of truth.
Execute Phase A2 per-operation preview pack only.
Lanes:
1. Preview artifact generation implementation.
2. CLI/report integration.
3. FFmpeg-gated and pure unit tests.
4. Docs, SDD, fix-log, final verification.
Use uv for tests. Do not track .omx. Commit with Lore protocol only after green verification.
"
```

## Team verification path
- Worker targeted tests for changed surfaces.
- Leader full `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider`.
- Leader compileall.
- `git ls-files .omx` must be empty.
- `git log --format=%B | grep -i Co-authored-by` must be empty.
- Push only after green verification.

## Goal-mode suggestion
Use `$ultragoal` if the user wants to track all A1–A8 phases as durable milestones. Use `$performance-goal` only for render speed/throughput tuning. Use `$autoresearch-goal` only if comparing ASR/diarization engines becomes a research task.
