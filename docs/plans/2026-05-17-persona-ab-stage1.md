# Plan: Persona A + B Stage 1 — local-first wedge

Date: 2026-05-17
Track: post-MVP usability + differentiation increment
Source research: `docs/research/2026-05-17-competitor-landscape.md`
Predecessors: `docs/sdd/podcast-auto-editor-mvp.md`, `docs/plans/2026-05-13-interface-roadmap.md`, `docs/plans/2026-05-13-ralplan-development-roadmap.md`

## Goal

Move the project from "engineer-only toolbox with end-to-end happy path" to "the only local-first podcast post tool that ships review-first AI edits and reproducible edit recipes" — without forcing a multi-track timeline rewrite.

## Personas (target)

- **Persona A — solo hobbyist podcaster** (1 episode/week, 30-60 min, USB mic, wants low cost + low learning curve).
- **Persona B — two-host conversation show** (1 episode/week, 60-90 min, remote dual-track from Riverside/SquadCast or in-room dual mic, post handed off to a producer).

Out of scope for this stage: full multitrack DAW, cloud multi-host recording, voice cloning, publishing integration.

## Strategic wedge (from research)

Three intersecting gaps no current product owns simultaneously:

1. **Local-first AI** (Descript/Riverside/Cleanvoice/Castmagic all upload; only Hindenburg/Reaper/Audacity stay local but lack AI).
2. **Per-edit review / diff UX** (only Resound + DAWs have it; cloud editors apply changes globally).
3. **Reproducible edit recipes** (no competitor exposes the edit graph as a git-checkable artefact).

Persona D (privacy-sensitive) and Persona E (hacker / DIY) are already served by the existing CLI, so this stage focuses on extending coverage to A + B without losing what D + E already get.

## Stage 1 PR sequence

PRs are ordered by leverage × dependency. Each is sized to land independently with full verification (`pytest`, `compileall`, `smoke.sh`) green and `git ls-files .omx` empty.

| Order | PR | Goal | Persona impact | Risk |
|---|---|---|---|---|
| 1 | PR-A | Real-podcast end-to-end run + fix-log | A, B, D, E | Low |
| 2 | PR-H | README messaging rewrite (`no metering / no credits / no upload / reproducible / offline`) | A, C, D | Trivial (docs) |
| 3 | PR-B | Dashboard upgrade — focus on diff / preview / accept-reject usability | A, B, C | Medium |
| 4 | PR-G | `recipe export/import` — git-friendly canonical edit recipe | C, D, E | Low |
| 5 | PR-C | Local diarization (`pyannote-audio` or `WhisperX`) | A (interview eps), B (mandatory), C | Medium-high |
| 6 | PR-D | AI draft attributes show-notes / chapters per speaker | A, B, C | Low (depends on PR-C) |
| 7 | PR-E | Per-speaker filler / backchannel detection | A (interview eps), B | Medium (depends on PR-C) |
| 8 | PR-F | Installer / quickstart + demo media | A, E | Medium |

Estimated wall time: 4-6 weeks at the current cadence (1 PR / 2-4 days).

---

### PR-A — Real-podcast end-to-end run + fix-log

**Why first:** 185 tests pass on synthetic fixtures, but no real podcast episode has been driven through the full pipeline (`ingest → ai draft → review → render → export`). Every following PR builds on an unverified foundation otherwise.

**Scope:**
- Pick one real episode (CC-licensed or own recording, 30-60 min).
- Run the full pipeline end-to-end with `--accept-safe-defaults` only for deterministic silence; review the AI draft and retake suggestions manually; export.
- Capture timing, surprises, output quality, regressions, and any operator confusion in `docs/fix-logs/2026-05-17-real-episode-e2e.md`.
- File any bugs found; fix only blocking ones in this PR (others become follow-up issues).

**Acceptance:**
- One end-to-end run artefact set committed under `docs/examples/<slug>/` (or pointer to a local-only path with redacted summary in the fix-log if licensing forbids checking the audio in).
- Fix-log lists every observed defect, classified as blocker / follow-up / cosmetic.
- All four verification commands green.

**Out of scope:** Fixing every defect; that becomes follow-up PRs.

---

### PR-H — README messaging rewrite

**Why second:** Zero engineering, immediate differentiation, time-sensitive. Descript's Sept-2025 repricing put pricing pain at the top of `r/podcasting` complaints; the messaging window is open now.

**Scope:**
- Rewrite README hero section + first 100 lines to lead with: *no metering, no credits, no upload, reproducible, offline-capable*.
- Add a short "What this is / what this isn't" section that explicitly says: not a DAW replacement, not a cloud recorder, no voice cloning.
- Add comparison snippet (1 short table) sourced from `docs/research/2026-05-17-competitor-landscape.md`.
- Mirror to `README.zh-TW.md` (per AGENTS.md §9).

**Acceptance:**
- `git diff README.md README.zh-TW.md` is the only change (no code touched).
- Messaging passes a "5-second test": opening README makes the wedge obvious without scrolling.
- Existing tests still green (no behavior change expected).

**Out of scope:** Marketing site, blog post, social copy.

---

### PR-B — Dashboard diff / preview / accept-reject upgrade

**Why third:** Research identifies *per-edit review/diff UX* as a market gap (only Resound + DAWs have it). The current dashboard shows status + AI draft links but doesn't yet make the diff/review path obvious or fast for non-engineers.

**Scope:**
- Audit current `review serve` dashboard against the diff-UX gap: what does a Persona A user see when they want to inspect a single proposed cut?
- Add to the dashboard:
  - per-operation diff view (before/after preview audio inline if present, transcript context, risk + confidence, detector reason, accept / reject / undo buttons calling the existing review-session API).
  - "next operation" button keyboard-friendly (`j` / `k` / `enter`).
  - Bulk filters: show only proposed / only retake / only speech-cut / only by risk.
- No new dependencies; stay on stdlib `http.server` + static HTML/JS per `interface-roadmap.md`.

**Acceptance:**
- A first-time user can complete one full review pass (proposed → accept/reject all → render-ready) without opening the CLI.
- New tests cover: per-operation diff endpoint serializes preview refs, accept/reject endpoint round-trips through `review_session.py`, keyboard nav doesn't break HTML escaping.
- Localhost-only constraint preserved.

**Out of scope:** WebSocket, multi-user, account system, anything that breaks "single-user localhost".

---

### PR-G — `recipe export/import` (git-friendly edit recipe)

**Why fourth:** The reproducibility wedge (item 3 in strategic wedge) is currently *implicit* — `timeline.v1` + recovery + provenance already cover most of it, but there is no single command to extract / replay a recipe. Without explicit surface area, no user will discover the differentiator.

**Scope:**
- New CLI: `podcast-auto-editor recipe export --run RUN_DIR --out recipe.v1.yaml` (or `.json`).
  - Emits a self-contained, deterministic, machine + human readable edit recipe: source media reference (path + sha256), config snapshot, full operation list with provenance, AI draft references (artefact path), quality gate targets, software version + commit hash.
- New CLI: `podcast-auto-editor recipe apply --recipe recipe.v1.yaml --media SOURCE.wav --out RUN_DIR_2`.
  - Replays the recipe deterministically; fails fast on media-hash mismatch unless `--allow-media-drift`.
- Document recipe schema in `docs/sdd/`.

**Acceptance:**
- Round-trip property test: random valid run → export → apply → byte-identical render (within FFmpeg determinism tolerance).
- Recipe diff is human-readable (a reviewer can `git diff recipe.v1.yaml` and understand the change).
- README updated with one-paragraph "edit-as-code" example.

**Out of scope:** Recipe migration across schema versions; remote recipe fetch.

---

### PR-C — Local diarization

**Why fifth:** Diarization is the dependency for PR-D and PR-E. Researching candidates: `pyannote-audio` (de-facto baseline, requires HF auth for some pretrained pipelines), `WhisperX` (combines whisper + pyannote + alignment, can run fully local once weights are cached), `NVIDIA NeMo` (heavier, gated by CUDA).

**Scope:**
- Decide between `pyannote-audio` and `WhisperX` based on: license, local-only operation, dependency weight, CPU vs GPU, accuracy on 2-speaker conversational audio.
- Add `podcast-auto-editor diarize` CLI: input audio + (optional) existing transcript, output `speaker_segments.v1.json` (start, end, speaker_id, confidence).
- Integrate diarization output into transcript import: `transcript.v1` cues gain optional `speaker_id` field.
- Ensure offline operation: weights downloaded once and cached locally; no per-run network call after first setup; document the one-time download in README.
- Provide a no-network test path (similar to AI dry-prompt pattern).

**Acceptance:**
- Two-speaker fixture audio yields ≥ 90% speaker-attribution accuracy on a manually labelled 5-minute clip.
- `podcast-auto-editor diarize --no-net` works after model cache exists; fails clearly without it.
- No `Co-authored-by` trailers, `.omx` clean, all four verification commands green.

**Out of scope:** Speaker identification by name; cross-episode speaker identity.

**Risk:** This PR introduces a heavy dependency. If both candidates fail the local-only or weight-caching test, escalate before continuing.

---

### PR-D — AI draft attributes per speaker

**Depends on:** PR-C.

**Scope:**
- `ai draft` reads `speaker_segments.v1.json` if present; chapters / show notes / summary cite speakers (e.g. `Host: ...`, `Guest: ...` or labels chosen by the user).
- Retake / speech-cut explanations include speaker context.
- Dashboard shows speaker label per operation.

**Acceptance:**
- Draft for a 2-speaker fixture mentions both speakers with non-trivial attribution.
- Existing single-speaker behaviour unchanged when no diarization output present.

---

### PR-E — Per-speaker filler / backchannel detection

**Depends on:** PR-C.

**Scope:**
- Speech-cut heuristic gains a per-speaker mode: same filler word can be aggressive on host A track and conservative on guest B track.
- Backchannel detection ("uh-huh", "right", "對對對") proposed as a separate operation type, never auto-accepted.
- Per-show config (YAML) accepts per-speaker overrides.

**Acceptance:**
- Backchannel proposals are clearly distinct from filler and visible in the dashboard.
- Per-speaker config drives different cut counts on the same fixture.

**Out of scope:** Online learning / fine-tuning. Keep this rule + heuristic + LLM-judge based.

---

### PR-F — Installer / quickstart + demo media

**Why last:** Persona A landing requires zero-friction install. Doing this earlier wastes work because PR-C will add a heavy diarization dependency; the installer needs to handle that.

**Scope:**
- One-command bootstrap: `pipx install podcast-auto-editor` or shell installer that wraps `uv` setup + first-run model cache priming.
- `podcast-auto-editor quickstart` command: downloads or unpacks demo media, runs full pipeline, opens dashboard at the end.
- Document the install flow for macOS / Linux / WSL.
- Verify install on a clean container.

**Acceptance:**
- A user can go from "git clone fresh" or "pipx install" to "open dashboard with demo episode" in under 10 minutes (excluding one-time model downloads).
- Smoke test for the installer is included in `scripts/`.

**Out of scope:** Windows native installer (WSL is acceptable for now), homebrew tap, signed binaries.

---

## Cross-PR constraints

- No new runtime dependencies without justification in the PR body and acceptance criteria for "still works offline after first setup".
- All audio-affecting operations stay `proposed` by default. Auto-accept rules from SDD §"Safety policy" remain authoritative.
- `.omx/`, `runs/`, `artifacts/`, demo audio (unless CC-licensed and small) stay untracked.
- No `Co-authored-by` trailers unless explicitly requested.
- Each PR ships its own `docs/fix-logs/<date>-<slug>.md` summarising what changed and why.

## Verification gate (per PR)

```
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor ./scripts/smoke.sh
git ls-files .omx   # must be empty
```

## Stage 2 / 3 (out of scope, recorded for context)

- **Stage 2 (Persona B "pseudo multi-track"):** `multi-ingest` CLI + cross-correlation alignment + per-track LUFS + `mix-down`. Each track runs the existing single-track pipeline; no schema change. Triggered when Stage 1 PR-C proves diarization works and a real Persona B user reports "OK but I want it to handle two files".
- **Stage 3 (real multi-track timeline):** `timeline.v2` with `affected_tracks` per operation, bleed / cross-talk-aware proposals, per-host editing weights. Only justified once Stage 2 has hit user feedback that a single-track timeline-per-track model is the bottleneck.

## Decision triggers to revisit this plan

- PR-A finds a critical regression in the existing pipeline → halt new PRs, fix first.
- PR-C decision (pyannote vs WhisperX) requires a new heavy dependency the user does not want → drop diarization from Stage 1, push PR-D and PR-E to Stage 2.
- A real Persona B user provides feedback before Stage 1 is complete → re-prioritise Stage 2 ahead of remaining Stage 1 PRs.
- Audacity OpenVINO local AI matures faster than expected → revisit positioning; the "free + local + AI" position is no longer empty.
