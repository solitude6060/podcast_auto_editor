# RALPLAN-DR: Podcast Auto Editor Development Roadmap

## Scope
Plan the remaining development actions for `podcast_auto_editor` after the MVP, team follow-up, and the current undo workflow increment. This plan is execution-ready for Ralph or OMX Team without requiring user decisions.

## Current evidence baseline
- Package modules: `podcast_auto_editor/{cli,pipeline,media,timeline,artifacts,transcript,fixtures,...}.py`.
- Tests: 48 passing on `origin/main` before the undo increment; targeted undo tests pass locally.
- Dev environment: `uv` with `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor`.
- Git constraints: `.omx/` ignored/local-only; no `Co-authored-by` trailers.

## RALPLAN-DR summary

### Principles
1. Preserve audio-first, local-first, no-cloud behavior.
2. Make every destructive edit reversible and auditable before render.
3. Prefer timeline-level determinism before FFmpeg media mutation.
4. Add tests before code and keep changes small enough for review.
5. Do not add dependencies unless a roadmap item explicitly justifies them.

### Decision drivers
1. Publishable-quality output with trustworthy safety gates.
2. Producer confidence: inspect, accept, undo, and reproduce edits.
3. Execution reliability under uv, CLI, and optional FFmpeg availability.

### Viable options considered
- **Option A: Hardening-first roadmap (chosen).** Finish undo, validation, dry-run/reporting, then expand media capabilities. Pros: lowers safety risk and stabilizes core abstractions. Cons: slower to add flashy AI features.
- **Option B: Feature-first roadmap.** Add ASR/diarization/AI mistake removal immediately. Pros: more visible automation. Cons: builds on less mature audit/recovery flows and raises false-positive risk.
- **Option C: UI-first roadmap.** Build a GUI around current CLI. Pros: producer-friendly. Cons: creates surface area before CLI contracts are stable.

## ADR

### Decision
Adopt Option A: complete reversible workflow and validation/reporting hardening before adding higher-risk AI/audio features or UI.

### Drivers
- Existing user requirements emphasize low-risk AI edits, preview/diff/recovery, publishable quality, and no unsafe automation.
- Current code already has good timeline/recovery primitives; the highest leverage is making them directly operable and test-backed.
- A stable CLI contract will make later team-parallel work safer.

### Alternatives considered
- Add ASR/diarization now: deferred until transcript import, recovery, and reporting are complete.
- Build web/GUI now: deferred until CLI workflows and artifacts are stable.
- Replace timeline schema: rejected because `timeline.v1` is sufficient for near-term hardening.

### Consequences
- Near-term work focuses on correctness, recovery, validation, and observability.
- Feature velocity is paced by safety gates and test coverage.
- Future AI lanes can plug into stable timeline/review abstractions.

### Follow-ups
Use the phases below as the canonical execution backlog.

## Execution roadmap

### Phase 0 — Finish current undo workflow increment
**Goal:** Make recovery actionable from CLI.

Files:
- `podcast_auto_editor/pipeline.py`
- `podcast_auto_editor/cli.py`
- `tests/test_artifacts_subtitles_pipeline.py`
- `tests/test_cli.py`
- `docs/plans/2026-05-13-undo-review-workflow.md`
- `docs/fix-logs/2026-05-13-undo-review-workflow.md`
- `README.md`, `docs/sdd/podcast-auto-editor-mvp.md`

Acceptance:
- `undo` requires `--all` or selected `--operation-id`.
- Selected accepted operations return to `proposed` with undo provenance.
- Non-accepted selected operations fail clearly.
- Recovery maps are rebuilt.

Verification:
- Targeted CLI/pipeline tests pass.
- Full uv pytest and compileall pass.

### Phase 1 — Validation hardening and schema contracts
**Goal:** Make invalid timelines/transcripts/config fail before media processing.

Actions:
1. Add strict timeline validation for source ranges in bounds, affected track IDs, confidence range, and overlapping accepted cuts.
2. Add config validation for negative/invalid thresholds and output formats.
3. Add transcript duration-bound validation when media duration is known.
4. Add `validate-run` command that validates config + timeline + transcript inputs together.

Acceptance:
- Invalid ranges/track refs/confidence are rejected.
- Overlapping accepted cuts fail before render.
- Config errors are actionable CLI messages.

### Phase 2 — Dry-run and run report workflow
**Goal:** Let producers inspect exact planned changes before render.

Actions:
1. Add `plan-run` or `dry-run` command that writes proposed timeline, diff, recovery, and summary without rendering media.
2. Add machine-readable run report summarizing operations, quality gates, derived assets, and warnings.
3. Add CLI `report` command to render Markdown/JSON from an accepted timeline/run directory.

Acceptance:
- Dry-run never writes exports.
- Report includes operation counts, removed duration, quality status, transcript/subtitle warnings, and restore instructions.

### Phase 3 — Preview fidelity improvements
**Goal:** Make previews useful enough for human acceptance decisions.

Actions:
1. Generate removed-segments preview that concatenates removed audio only, not just a source excerpt.
2. Generate before/after preview around each edit with configurable padding.
3. Include per-operation preview refs in timeline/diff metadata.
4. Add FFmpeg integration tests gated by tool availability.

Acceptance:
- Preview files correspond to actual edit ranges.
- Missing FFmpeg produces clear errors; pure unit tests remain tool-independent.

### Phase 4 — Quality gate expansion
**Goal:** Improve publishable-quality confidence.

Actions:
1. Persist raw `loudnorm` metrics and normalized output target metadata.
2. Add optional WAV and MP3 export paths with quality checks for each export.
3. Add failed-gate report that blocks success exit unless explicitly allowed for diagnostics.
4. Add sample-rate/channel normalization tests.

Acceptance:
- Quality report identifies which export failed and why.
- Render success requires all required quality gates to pass.

### Phase 5 — Safer AI-assisted edit proposals
**Goal:** Add higher-level mistake/retake proposals without unsafe deletion.

Actions:
1. Extend transcript heuristics for filler words, false starts, and repeated phrases as proposed-only operations.
2. Add confidence/risk scoring explainability in provenance.
3. Keep auto-accept disabled except deterministic silence and already-approved low-risk policy.
4. Add review commands for accept/reject/undo with audit trail.

Acceptance:
- All speech-changing operations default to `proposed`.
- Provenance explains detector, evidence text, confidence, and reason.

### Phase 6 — Optional video sync/export hardening
**Goal:** Keep optional video reliable without complex multicam.

Actions:
1. Validate stream presence, durations, timebase, and drift before render.
2. Add post-render sync report with source and output durations.
3. Add MP4 fixture tests for cut ranges and drift failures.

Acceptance:
- Missing/unmeasured stream durations fail clearly.
- Edited MP4 sync gate remains within tolerance.

### Phase 7 — Packaging and operational polish
**Goal:** Make local installation and usage reproducible.

Actions:
1. Add documented `uv sync --group dev` workflow.
2. Add CLI help examples and sample transcript JSON docs.
3. Add smoke-test script using demo fixtures.
4. Consider GitHub Actions only if user later wants CI; until then keep local uv verification authoritative.

Acceptance:
- A fresh clone can run tests and demo fixtures from README instructions.

## Available-agent-types roster
Use only available repo/OMX roles:
- `planner` — phase sequencing and acceptance criteria.
- `architect` — timeline/media boundary review.
- `executor` — implementation lanes.
- `test-engineer` — regression and FFmpeg-gated tests.
- `verifier` — final evidence and artifact audit.
- `code-reviewer` — safety and maintainability review.
- `writer` — README/SDD/fix-log updates.

## Ralph follow-up guidance
Use Ralph for sequential completion when prioritizing safety over speed:

```bash
omx ralph "Execute docs/plans/2026-05-13-ralplan-development-roadmap.md Phase 0, then Phase 1 only. Follow strict SDD/TDD, uv verification, Lore commits, no .omx push, no Co-authored-by trailers."
```

Suggested Ralph lane:
- `executor` medium reasoning for implementation.
- `verifier` high reasoning for final proof.
- `code-reviewer` high reasoning if touching media render safety.

## Team follow-up guidance
Use OMX team for phases with independent lanes:

```bash
OMX_TEAM_WORKER_CLI=codex omx team 4:executor "
Use docs/plans/2026-05-13-ralplan-development-roadmap.md as source of truth.
Execute Phase 1 and Phase 2 only.
Lanes:
1. Timeline/config validation hardening.
2. Transcript duration validation and validate-run CLI.
3. Dry-run/report command and artifacts.
4. QA/docs/verification lane.
Use uv for tests. Do not track .omx. Commit with Lore protocol only after green verification.
"
```

Team verification path:
- Each worker reports targeted tests and changed files.
- Leader runs full uv pytest + compileall.
- Leader checks `git ls-files .omx` empty and no `Co-authored-by` trailers.
- Leader squashes/normalizes team checkpoint commits if needed before push.

## Goal-mode suggestions
- `$ultragoal`: best fit for durable multi-phase implementation tracking across this roadmap.
- `$performance-goal`: use later only for measurable render speed/latency optimization.
- `$autoresearch-goal`: not currently needed; this is implementation delivery, not research.

## Critic gate
This roadmap is acceptable only if execution never skips:
- failing tests before implementation,
- uv verification before commit,
- recovery/safety audit for edit-changing features,
- docs/fix-log updates for each phase.
