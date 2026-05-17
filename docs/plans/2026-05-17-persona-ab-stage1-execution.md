# Stage 1 — detailed execution plan

Date: 2026-05-17
Companion to: `docs/plans/2026-05-17-persona-ab-stage1.md`
Source research: `docs/research/2026-05-17-competitor-landscape.md`
Predecessor PR: PR-A (#26) merged 2026-05-17 — synthetic walkthrough + review-session CLI fix.

This document breaks each remaining Stage 1 PR (H, G, B, C, D, E, F) into commit-level tasks, exact file paths, named tests, locked pre-flight decisions, and known blockers. After this plan lands, each PR is executable without further research.

## Pre-flight decisions (locked, no more research)

| Decision | Choice | Reason |
|---|---|---|
| Diarization model family | `pyannote-audio` 3.x community pipeline as the real provider; ship a `mock` provider in the same interface so the CLI lands without a HuggingFace token | `WhisperX` uses pyannote underneath anyway; `pyannote` 3.x has the most active CPU path; mock provider keeps the test suite no-network and lets the CLI ship before a real-audio verification round |
| HuggingFace token handling | Read from `HF_TOKEN` env var; never hardcoded; never committed | AGENTS.md §8 |
| Real-provider dependency install | Lazy import inside the `pyannote` adapter; raise a clear `DiarizationProviderError` with install instructions if `pyannote-audio` is absent | Keeps the base install free of a 1+ GB ML dep; matches existing `transcribe` ASR provider pattern |
| Recipe schema version | `recipe.v1.yaml` (YAML + JSON both supported, YAML default for human review) | Existing artefacts use JSON; YAML round-trips cleanly via `pyyaml` — but `pyyaml` is a new dependency. Drop YAML, ship JSON-only (`recipe.v1.json`) to keep "no new deps" |
| Recipe schema version (revised) | `recipe.v1.json` only; no YAML | No new dependencies (constraint from Stage 1 plan) |
| Dashboard accept/reject keyboard nav | Pure stdlib HTML/JS, no JS framework | `interface-roadmap.md` UI-3 constraint |
| Installer target OS this round | Linux + `uv`; document macOS / WSL paths but mark them as unverified | I have Linux locally; the user can confirm macOS / WSL later |
| README messaging language | English first, mirror to `README.zh-TW.md` | AGENTS.md §9 |

## Execution order

```
[done] PR-A (#26)
        ↓
PR (this plan)                      → docs only, self-merge after CI green
        ↓
PR-H  README messaging              → docs only, self-merge after CI green
        ↓
PR-G  recipe export/import          → code, full triple-review
        ↓
PR-B  dashboard diff/preview UX     → code, full triple-review
        ↓
PR-C  diarization CLI + mock        → code, full triple-review;
                                       real provider integration deferred
        ↓
PR-D  AI draft attributes per       → code, full triple-review
      speaker (depends on PR-C)
        ↓
PR-E  per-speaker filler /          → code, full triple-review
      backchannel (depends on PR-C)
        ↓
PR-F  installer / quickstart        → code, full triple-review
      Linux+uv path only
        ↓
[user follow-up]
- supply HuggingFace token + a real 2-speaker recording
  → PR-C2: real pyannote integration + diarization accuracy
    measurement
- verify installer on macOS / WSL
  → PR-F2: installer fixes for those platforms
```

Each PR runs under Workflow Mini (docs only) or Workflow A/D (code) per `workflow-routing` skill. Code PRs go through `/triple-review` per the project's review protocol.

---

## PR-H — README messaging rewrite (no metering, no upload, reproducible)

### Goal
Rewrite the top of `README.md` (and the mirrored `README.zh-TW.md`) so a first-time reader sees the wedge in five seconds: local-first, free, no upload, no metered credits, no AI vendor lock-in.

### Pre-flight decisions
- Lead the hero section with four bullets that are concrete promises, not slogans: "Runs entirely on your laptop. No accounts. No subscription. No audio leaves the disk."
- Add a comparison snippet pulled from `docs/research/2026-05-17-competitor-landscape.md` (Descript / Riverside / Cleanvoice / us in 4 columns; 6 rows).
- Add a one-paragraph "What this is / what this is not" section: not a DAW replacement; not a cloud recorder; no voice cloning.
- Keep all existing content below; only the first ~120 lines change.

### Commit plan
1. `docs:` rewrite README hero + comparison snippet + "what this is / what this is not"; mirror to `README.zh-TW.md`.

### Files
- `README.md` — top ~120 lines.
- `README.zh-TW.md` — same.

### Tests
None — docs only, no behaviour change.

### Acceptance
- `git diff README.md README.zh-TW.md` is the only change.
- Reader can articulate the wedge after reading the first 30 seconds.
- All four verification gates still green (no behaviour change, so they should be unaffected).
- Mirroring discipline: every English bullet has a Chinese equivalent.

### Out of scope
- Marketing site, blog post, social copy, screenshots.
- Comparison rows that aren't already in the competitor research doc.

### Risk
- None practical. Docs-only PR.

---

## PR-G — `recipe export/import` (git-friendly canonical edit recipe)

### Goal
Surface the existing `timeline.v1` + recovery + provenance + AI draft data as a single, deterministic, human-readable `recipe.v1.json` artefact that another user can replay against the same source audio to reproduce the edit. This is the "edit-as-code" feature; no current competitor ships it.

### Pre-flight decisions
- Format: JSON only (`recipe.v1.json`) — no YAML, since `pyyaml` would be a new dep.
- Recipe fields (schema):
  ```json
  {
    "schema_version": "recipe.v1",
    "source_media": {"path": "...", "sha256": "...", "duration_s": 1234.5},
    "config": { ... },
    "operations": [ ... per-operation provenance entries ... ],
    "ai_draft_ref": "ai/ai-draft.v1.json" or null,
    "quality_gate": { ... LUFS/true-peak targets ... },
    "software": {"version": "<package version>", "git_sha": "..."}
  }
  ```
- Source media: stored as path + sha256 + duration; never embedded.
- `apply` failure modes: media-hash mismatch raises unless `--allow-media-drift`; missing source file raises.

### Commit plan
1. `test:` add red regression tests for: round-trip property (run → export → apply → identical recipe), media-hash mismatch refused, `--allow-media-drift` overrides the refusal, missing source path raises clearly.
2. `feat:` add `podcast-auto-editor recipe export` and `recipe apply` CLI subcommands; add `podcast_auto_editor/recipe.py` module.
3. `docs:` README section "Reproducible edits with `recipe export`"; mirror to zh-TW.

### Files
- New: `podcast_auto_editor/recipe.py` — schema + export() + apply() + media-hash check.
- Modified: `podcast_auto_editor/cli.py` — add `recipe` subparser + handler.
- New: `tests/test_recipe.py` — round-trip + mismatch + missing-source tests.
- Modified: `README.md` + `README.zh-TW.md`.
- Modified: `CHANGELOG.md` + `CHANGELOG.zh-TW.md`.

### Tests
- `test_recipe_export_writes_canonical_json`
- `test_recipe_apply_replays_deterministically_when_hash_matches`
- `test_recipe_apply_refuses_when_media_hash_mismatch`
- `test_recipe_apply_with_allow_media_drift_overrides_refusal`
- `test_recipe_apply_raises_when_source_path_missing`

### Acceptance
- `podcast-auto-editor recipe export --run RUN_DIR --out recipe.v1.json` produces a self-contained artefact.
- `podcast-auto-editor recipe apply --recipe recipe.v1.json --media SOURCE.wav --out RUN_DIR_2` replays the same edits; the resulting `timeline.proposed.v1.json` is byte-identical to the original.
- Round-trip property test green on a synthetic fixture.
- All four verification gates green.

### Out of scope
- Cross-schema migration (`recipe.v0` → `recipe.v1`).
- Remote recipe fetch.
- YAML format support.

### Risk
- Determinism on a fresh OS / different FFmpeg version — call out in the recipe metadata.
- `git_sha` lookup at export time: handle the "not a git repo" case cleanly.

---

## PR-B — Dashboard diff / preview / accept-reject upgrade

### Goal
Make the localhost review dashboard usable for a non-engineer. Today it serves status + artifact links; producers still have to read JSON to decide on each operation. After PR-B, the dashboard exposes per-operation diff context inline and keyboard navigation, so a producer can accept/reject through one full episode without opening the CLI.

### Pre-flight decisions
- Stay on stdlib `http.server` + static HTML/JS (no JS framework, no new deps) — `interface-roadmap.md` UI-3 constraint.
- Keyboard nav: `j` / `k` to move next/prev; `a` accept; `r` reject; `u` undo. All readable from JS `keydown`.
- Per-operation diff endpoint: `GET /api/operation/<operation_id>` returns the operation payload + preview refs + risk/confidence/detector reason.
- Filter buttons: "all / proposed / accepted / rejected / retake / speech / silence" — server-side filtering, not client-side, to keep the wire payload small.
- Localhost-only constraint preserved (no new bindings).

### Commit plan
1. `test:` red tests for: `/api/operation/<id>` endpoint returns 200 + correct payload, returns 404 for unknown id, returns 404 for path-traversal attempts; filter param narrows the list; keyboard event handlers exist in the rendered HTML.
2. `feat:` extend `local_review_server.py` with the new endpoint + filter + keyboard handlers in the HTML.
3. `docs:` README section update for `review serve`; mirror to zh-TW.

### Files
- Modified: `podcast_auto_editor/local_review_server.py` — add `/api/operation/<id>`, filter param on `/api/status`, new HTML/JS for keyboard nav and per-op detail pane.
- Modified: `tests/test_local_review_server.py` — new HTTP-level tests.
- Modified: `README.md` + `README.zh-TW.md` — short section update.
- Modified: `CHANGELOG.md` + `CHANGELOG.zh-TW.md`.

### Tests
- `test_dashboard_operation_endpoint_returns_payload_for_known_id`
- `test_dashboard_operation_endpoint_404s_for_unknown_id`
- `test_dashboard_operation_endpoint_rejects_path_traversal`
- `test_dashboard_status_filter_param_narrows_list`
- `test_dashboard_html_contains_keyboard_handlers`

### Acceptance
- A first-time user can complete a full review pass (every proposed op → accept/reject) using only `j` / `k` / `a` / `r` / `u`.
- New endpoint returns JSON for valid ids, 404 for unknown or traversal, with the same `ARTIFACT_ALLOWLIST` discipline.
- All four verification gates green.

### Out of scope
- WebSocket / SSE for live updates.
- Multi-user / accounts.
- Anything that breaks "single-user localhost".

### Risk
- HTML string growth — keep the HTML still under ~10 KB.
- Keyboard handlers must not interfere with input fields (Reviewer / Note).

---

## PR-C — Diarization CLI interface + mock provider (real provider deferred)

### Goal
Land the `podcast-auto-editor diarize` CLI with a provider-pluggable interface and a built-in `mock` provider that returns synthetic speaker segments from a config dict. Ship the real `pyannote` adapter behind a lazy import so the CLI works without HuggingFace token until the user opts in. This unblocks PR-D and PR-E without requiring real audio in this round.

### Pre-flight decisions
- Provider interface: `DiarizationProvider` ABC in `podcast_auto_editor/diarization.py` with `diarize(audio_path, **options) -> SpeakerSegments`.
- Built-in providers:
  - `mock` — reads a JSON config of expected segments (or generates them deterministically from audio duration / channel count); ships in this PR.
  - `pyannote` — lazy `from pyannote.audio import Pipeline` inside the adapter; raises `DiarizationProviderError` with install instructions if missing; ships in this PR but is only exercised when user installs `pyannote-audio` and sets `HF_TOKEN`.
- Output schema: `speaker_segments.v1.json` with `[{"start": s, "end": s, "speaker_id": "spk0|spk1|...", "confidence": 0..1}]`. Distinct from `transcript.v1`.
- CLI: `podcast-auto-editor diarize INPUT --provider mock --out speaker_segments.v1.json --config diarization-config.json`.
- Transcript integration: `transcript.v1` cues gain an optional `speaker_id` field; existing transcripts without it stay valid (backward compatible).

### Commit plan
1. `test:` red tests for: mock provider returns the config-driven segments, `speaker_segments.v1` schema is round-trippable, real `pyannote` adapter raises a clear error when `pyannote-audio` not installed, transcript `speaker_id` field is optional and preserved through validation.
2. `feat:` add `podcast_auto_editor/diarization.py` with ABC + mock + lazy pyannote adapter; add CLI subcommand; extend transcript schema to allow optional `speaker_id`.
3. `docs:` README section "Diarization (optional)"; mirror to zh-TW; note that real diarization requires `uv add pyannote-audio` + `HF_TOKEN`.

### Files
- New: `podcast_auto_editor/diarization.py` — ABC + `MockDiarizationProvider` + `PyannoteDiarizationProvider` (lazy import) + `diarize_to_file()`.
- Modified: `podcast_auto_editor/cli.py` — add `diarize` subparser.
- Modified: `podcast_auto_editor/transcript.py` — optional `speaker_id` on cues.
- New: `tests/test_diarization.py` — mock provider tests + pyannote lazy-error tests.
- Modified: `README.md` + `README.zh-TW.md`.
- Modified: `CHANGELOG.md` + `CHANGELOG.zh-TW.md`.

### Tests
- `test_mock_diarization_returns_configured_segments`
- `test_speaker_segments_v1_round_trip`
- `test_pyannote_adapter_raises_clear_error_when_dependency_missing`
- `test_transcript_v1_accepts_optional_speaker_id`
- `test_transcript_v1_validation_passes_without_speaker_id`

### Acceptance
- `podcast-auto-editor diarize SAMPLE.wav --provider mock --config two-speaker.json --out speaker_segments.v1.json` produces a valid artefact in CI (no network, no GPU, no HF token).
- `podcast-auto-editor diarize SAMPLE.wav --provider pyannote ...` fails fast with `DiarizationProviderError: pyannote-audio not installed; uv add pyannote-audio and set HF_TOKEN` when the dep is absent.
- All four verification gates green.

### Out of scope (deferred to follow-up PR-C2 once user supplies token + audio)
- Real `pyannote` model load + actual diarization on a real recording.
- 90% accuracy verification on a 2-speaker fixture (the acceptance target in the original plan).
- Tuning the pyannote pipeline parameters (clustering threshold etc).

### Risk
- Lazy import discipline — adapter must not fail at module import time if `pyannote-audio` is missing.
- `speaker_segments.v1` schema choice — must be compatible with PR-D / PR-E without revisions.

---

## PR-D — AI draft attributes per speaker (depends on PR-C)

### Goal
When `speaker_segments.v1.json` is present in the run dir, `ai draft` reads it and attaches a speaker label to each chapter, show-note line, and operation explanation. When absent, behaviour is unchanged. No retake/speech-cut auto-acceptance changes.

### Pre-flight decisions
- Detection: `generate_ai_draft` looks for `<run_dir>/speaker_segments.v1.json` automatically; an explicit `--speaker-segments PATH` flag overrides.
- Prompt change: when speaker segments present, the prompt now includes a `Speakers: spk0=Host, spk1=Guest` mapping (user-configurable via CLI flag `--speaker-label spk0=Host`) and asks the LLM to attribute each chapter / show-note to a speaker.
- Output schema: `ai-draft.v1` chapters gain an optional `speaker_id`; show notes become objects `{"text": ..., "speaker_id": ...}` (with a backward-compat path for strings).
- Dashboard: per-operation panel displays the speaker label.

### Commit plan
1. `test:` red tests for: when `speaker_segments.v1.json` is present, the generated AI draft request prompt names the speakers; when absent, the existing single-speaker behaviour is preserved; user-provided `--speaker-label` overrides the default.
2. `feat:` extend `ai_drafts.py` to read speaker segments and produce per-speaker fields; update `local_review_server.py` to display them.
3. `docs:` README; mirror zh-TW.

### Files
- Modified: `podcast_auto_editor/ai_drafts.py`.
- Modified: `podcast_auto_editor/cli.py`.
- Modified: `podcast_auto_editor/local_review_server.py`.
- Modified: `tests/test_ai_drafts.py`.
- Modified: `README.md` + `README.zh-TW.md`.
- Modified: `CHANGELOG.md` + `CHANGELOG.zh-TW.md`.

### Tests
- `test_ai_draft_includes_speaker_segments_when_present`
- `test_ai_draft_falls_back_to_single_speaker_when_segments_absent`
- `test_speaker_label_override_replaces_default_labels`
- `test_dashboard_shows_speaker_label_for_operation_when_available`

### Acceptance
- Two-speaker mock fixture (from PR-C) produces an AI draft whose chapters / show-notes carry distinct `spk0` / `spk1` attribution.
- Single-speaker fixture (no `speaker_segments.v1.json`) produces the existing draft shape — backward compatible.
- All four verification gates green.

### Out of scope
- Real LLM quality assessment (still dry-prompt only in CI).
- Speaker name identification beyond user-supplied labels.

### Risk
- Schema drift between `ai-draft.v1` versions if backward compat isn't tested explicitly. Add explicit "single-speaker fixture still works" test.

---

## PR-E — Per-speaker filler / backchannel detection (depends on PR-C)

### Goal
The existing `speech_cut` heuristic gains a per-speaker mode: same filler word can be cut aggressively from host A and conservatively from guest B; backchannel utterances ("uh-huh", "right", "對對對") become a distinct proposed-only operation type so the producer can review them separately.

### Pre-flight decisions
- New operation type: `backchannel_cut` — same shape as `speech_cut` but a new `type` value; render gates treat it identically to `speech_cut` (never auto-accepted, requires explicit review).
- Per-speaker config: `config.diarization.per_speaker_overrides = {"spk0": {"filler_aggression": "high"}, "spk1": {"filler_aggression": "low"}}` in the existing config schema.
- Detection input: takes `transcript.v1` cues with `speaker_id`; falls back to "all one speaker" when no diarization info.

### Commit plan
1. `test:` red tests for: same filler text on different speakers produces different cut counts under per-speaker config; backchannel detection produces `backchannel_cut` ops never `speech_cut`; `backchannel_cut` ops are never auto-accepted at render time.
2. `feat:` extend `transcript.speech_cleanup_heuristic` and add `backchannel.heuristic`; extend render gate validation.
3. `docs:` README + zh-TW.

### Files
- Modified: `podcast_auto_editor/transcript.py` (or wherever the heuristic lives).
- Modified: `podcast_auto_editor/timeline.py` — `backchannel_cut` allowed in operation type set.
- Modified: `podcast_auto_editor/cli.py` — render gate.
- New / modified: `tests/test_transcript.py` (or wherever filler tests live).
- Modified: `README.md` + `README.zh-TW.md`.
- Modified: `CHANGELOG.md` + `CHANGELOG.zh-TW.md`.

### Tests
- `test_speech_cut_aggression_differs_by_speaker_config`
- `test_backchannel_detection_emits_backchannel_cut_type`
- `test_backchannel_cut_never_auto_accepted_at_render`
- `test_backchannel_cut_carries_provenance_with_detector_field`

### Acceptance
- Per-speaker config on a synthetic 2-speaker fixture produces visibly different cut counts.
- Backchannel ops are visible in the dashboard with their own filter chip.
- All four verification gates green.

### Out of scope
- ML model for filler detection (stay rule + LLM-judge based).
- Online learning from approved cuts.

### Risk
- Existing `speech_cut` tests must still pass — backward compatibility for runs without speaker segments.
- Render gate must explicitly cover `backchannel_cut` so it can't slip through accepted without review.

---

## PR-F — Installer / quickstart + demo media (Linux + uv only this round)

### Goal
A user can go from "fresh git clone" or `pipx install` to "open dashboard with a demo episode" in under 10 minutes on Linux with `uv` already installed.

### Pre-flight decisions
- Distribution: `pipx install podcast-auto-editor` (PyPI publish deferred; the installer script clones the repo and uses `uv run`).
- Bootstrap script: `scripts/install.sh` — checks for `uv`, runs `uv sync --group dev`, runs `demo-fixtures`, prints the dashboard URL.
- Quickstart command: `podcast-auto-editor quickstart` — runs end-to-end demo (the steps from PR-A walkthrough) and opens the dashboard.
- Verification target: Linux (Ubuntu 24.04 in CI / current host).
- macOS / WSL: documented but explicitly marked "unverified — please report" in README.

### Commit plan
1. `test:` red tests for: `quickstart` command exists in the parser; bootstrap script is executable + idempotent (running twice doesn't fail); demo-fixtures are deterministic across runs (already partially covered).
2. `feat:` add `scripts/install.sh` + `podcast-auto-editor quickstart` subcommand.
3. `docs:` README install section rewrite + quickstart walkthrough.

### Files
- New: `scripts/install.sh`.
- Modified: `podcast_auto_editor/cli.py` — `quickstart` subparser.
- Modified: `tests/test_cli.py` — quickstart command test.
- Modified: `README.md` + `README.zh-TW.md`.
- Modified: `CHANGELOG.md` + `CHANGELOG.zh-TW.md`.

### Tests
- `test_quickstart_command_exists_in_parser`
- `test_install_script_is_idempotent` (run twice, second run should not error)
- `test_install_script_handles_missing_uv_clearly` (when `uv` is not on PATH)

### Acceptance
- On Linux + `uv` installed: `bash scripts/install.sh && podcast-auto-editor quickstart` completes in under 10 minutes including the first-run model cache (no diarization model in this round — just FFmpeg fixtures).
- Re-running `install.sh` is idempotent.
- All four verification gates green.

### Out of scope (deferred to PR-F2)
- macOS native installer (Homebrew tap).
- Windows native installer.
- WSL-specific path quirks.
- PyPI publish workflow.
- Signed binaries.

### Risk
- `uv` version drift — pin a minimum version, document.
- Demo run on a freshly cloned tree must not fail when FFmpeg is absent — handle gracefully like the existing smoke script does.

---

## Cross-cutting constraints (all PRs)

These are pulled from AGENTS.md and the global CLAUDE.md so they don't need restating per PR.

- TDD: failing test first, minimal implementation second.
- Surgical changes: touch only what the task requires.
- All four verification gates green before push: `pytest -q -p no:cacheprovider`, `compileall`, `smoke.sh`, `git ls-files .omx` empty.
- No new runtime dependencies unless explicitly justified in the PR body and acceptance.
- `.omx/`, runs, artifacts, demo audio stay untracked.
- No `Co-authored-by` trailers.
- Lore commit protocol.
- Each PR ships its own `docs/fix-logs/<date>-<slug>.md` summarising what changed and why.
- Code PRs (G, B, C, D, E, F) go through `/triple-review`; doc PRs (this plan, H) self-merge after CI green.
- Branch from `dev`; merge back via PR; `dev → main` is a separate phase-completion PR (not Stage 1's job).

## Decision triggers to revisit this plan

- A real episode is supplied by the user → run the PR-A walkthrough again on real audio; insert a PR-A2 fix log; this may add or re-prioritise items.
- HuggingFace token + diarization weights become available → unblock PR-C2 (real provider integration) immediately after PR-C lands.
- macOS / WSL verification feedback → PR-F2.
- A reviewer (triple review) flags a structural issue with one PR's interface (e.g., `speaker_segments.v1` schema is wrong) → pause downstream PRs (D, E) until the upstream interface is right.
- Opus / Codex / Gemini quota hits red → fall back to a slimmer review per `workflow-routing` skill's elasticity gates.

## What "done" looks like for Stage 1

- All 7 PRs (H, G, B, C, D, E, F) merged into `dev`.
- README's first 30 seconds match the wedge described in the strategy.
- `recipe export/import` round-trips byte-identically on synthetic fixtures.
- Dashboard handles a complete review pass via keyboard only.
- `diarize` CLI works with mock provider; pyannote adapter is wired but waiting for token + audio.
- A user on a clean Linux box can `bash scripts/install.sh && podcast-auto-editor quickstart` in 10 minutes.
- All Stage 1 work passes the four verification gates on `dev`.
- A `dev → main` promotion PR follows immediately as the Stage 1 phase exit.
