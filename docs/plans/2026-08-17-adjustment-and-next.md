# Adjustment direction and next plan

Traditional Chinese: [`2026-08-17-adjustment-and-next.zh-TW.md`](2026-08-17-adjustment-and-next.zh-TW.md)

Date: 2026-08-17  
Inputs: `docs/sdd/podcast-auto-editor-mvp.md`, `docs/reviews/2026-08-17-project-status-review.md`, `docs/research/2026-08-17-competitor-landscape.md`, `user_todo.md`, `docs/plans/2026-05-17-persona-ab-stage1.md`  
Workflow: plan-file only. No implementation in this document.

**Phase 0 status (2026-08-17):** Landed on `docs/2026-08-17-status-sync` as `86d9560` (pyannote CUDA `.to` guard), `08a165b` (two-pass loudnorm / reports), `21e68ba` (docs sync). The 2026-05-18 quality patch was kept. 19 locked worktrees were left untouched. No version bump. No `dev` → `main`. No push/PR.

---

## First-principles audit

### 1. Need

- Stated request: review the repo, survey products/GitHub, give adjustment direction and a follow-up plan.
- Underlying need: a continue / adjust / stop decision for this side project, with a next action that can change that decision.
- Same? No. A 1.0 tag or another ASR provider does not change the decision. A real episode does.

### 2. Inherited assumption check

- Assumption that was about to win: "the backlog is MVP 1.0 sign-off plus remaining providers (Lattifai decode, UI previous-op, more AI)." Source: `user_todo.md` 2026-05-18.
- Verified for this case? No. `docs/fix-logs/2026-05-17-real-episode-e2e.md` used 4 s of silence. `docs/walkthroughs/real-podcast-ep1.md` still defaults to stub ASR. The walkthrough disk was unmounted on 2026-08-17.

### 3. Ground-truth verification

| Claim | Check | Result |
|---|---|---|
| Recipe is only planned | `README.md:21` vs `podcast_auto_editor/recipe.py` | Docs stale; code exists |
| This tool already does denoise | grep over `podcast_auto_editor/*.py` | No denoise module |
| Local CLI silence-cut is unoccupied | WyattBlue/auto-editor GitHub page 2026-08-17 | 4,984 stars; occupied |
| Per-edit review is unique | Resound homepage; Poddie/Redact READMEs | Unique only as *local + preview clips + recipe* |
| 324 tests collected | `pytest --collect-only` | True |
| Real audio path available today | `/media/ma/1AF83466F83441F5` | Missing |

### 4. Verdict

Valid build decision: freeze provider expansion; run the smallest real episode; then pick one wedge from that log.

Not a workaround: refusing `1.0.0` until that log exists.

### 5. Review

This plan is a knowledge artifact. Implementation PRs still need their own review.

---

## RALPLAN-DR summary

### Principles

1. Local-first, review-first, no silent speech edits.
2. Evidence before platform completeness.
3. Differentiate on recipe + review artifacts + measured publish gates + Chinese ASR, not on "CLI cuts silence".
4. One wedge after the first real run. Do not resume the provider matrix.
5. CLI remains the automation contract. Interfaces only consume run artifacts.

### Decision drivers

1. Can a real episode become publish-ready without leaving the machine?
2. Which failure actually appears: wrong cuts, bad transcript, failed LUFS, or unusable review UI?
3. Keep the safety policy in `docs/sdd/podcast-auto-editor-mvp.md`.

### Options

- **Option A — Evidence-first (chosen).** Hygiene, then one real episode, then one wedge. Matches the research-preliminary-evidence rule.
- **Option B — Ship 1.0 from `dev` now.** Rejected. Version would encode adapter count, not a shipped episode.
- **Option C — Build a local Descript (text editor).** Rejected. Poddie / Redact / Bowdler already occupy that sentence; star counts are 3–23, but the UX bet is the same.

---

## ADR

**Decision:** Adopt Option A. Stay on `0.1.x` (or `0.2.0` only after the real-episode fix-log). Do not open Lattifai decode, desktop packaging, denoise, or NLE export until that log names them as the blocker.

**Drivers:** 91 days since last commit; 324 tests and 161 markdown files; no publishable real-episode evidence; `auto-editor` occupies silence-cut CLI.

**Alternatives considered:** 1.0 tag; text-edit desktop; DeepFilterNet now.

**Why chosen:** The next continue / adjust / stop bit is a listened-to episode, not another adapter.

**Consequences:** `user_todo.md` B1–B3 are superseded. README must stop saying recipe is planned. `main` stays behind until the evidence PR is ready to promote.

**Follow-ups:** Phases 0–3 below.

---

## Requirements summary

1. Working tree is either committed on a feature branch off `dev`, or explicitly discarded.
2. README / SDD / comparison table match `dev` and the 2026-08-17 landscape.
3. One real spoken episode (prefer Mandarin, 10–30 min, rights owned) completes: non-stub ASR → `review serve` decisions → quality-gated export or a named gate failure.
4. A fix-log lists every defect as blocker / follow-up / cosmetic.
5. The next implementation PR implements only the top blocker from that log.

---

## Acceptance criteria (testable)

- `git status` on `dev` is clean, or the remaining dirty files are listed in `handover.md` with an owner decision.
- `README.md` comparison table includes `auto-editor` and marks `recipe.v1` as implemented.
- `docs/sdd/podcast-auto-editor-mvp.md` no longer cites "29 passed" as current verification.
- `docs/fix-logs/2026-08-XX-real-episode.md` exists and names: audio duration, ASR provider, operation counts by type, review decisions, export profile pass/fail with target vs actual LUFS / true peak.
- No new ASR / alignment / diarization provider is added in the same PR as the evidence run.
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` and `compileall` pass on the docs/hygiene PR. (Cache dir follows the project AGENTS.md command; it is scratch only.)

---

## Phase 0 — Hygiene (no behavior change except docs)

**Status:** done on `docs/2026-08-17-status-sync` (not yet pushed).

**Files:** `README.md`, `README.zh-TW.md`, `docs/sdd/podcast-auto-editor-mvp.md`, 2026-05-18 quality set, `status.md`, `tracker.md`, `handover.md`

Steps:

1. Branch from `dev`: `docs/2026-08-17-status-sync`. Quality patch kept on the same branch (`08a165b`) instead of a second `feature/podcaster-ready-quality` branch.
2. Read the uncommitted diff. Tests in `tests/test_exports.py` and `tests/test_media_sync.py` matched the patch; it was complete TDD work and was committed.
3. Rewrite the README comparison table: add `auto-editor`; set recipe to implemented; state denoise is not shipped.
4. Update SDD verification to current collect count and point at this review.
5. Leave the 19 `.claude/worktrees/` locked trees untouched until the user asks to remove them.

**Out of scope:** version bump, `dev` → `main` promotion.

---

## Phase 1 — Smallest real episode (the decision experiment)

**Files:** `docs/walkthroughs/real-podcast-ep1.md`, `docs/fix-logs/2026-08-XX-real-episode.md`, `scripts/walkthrough-real-podcast.sh`, possibly `pipeline.py` only if a blocker is found.

Operator inputs (required):

- A WAV/MP3 the user owns, not committed.
- One ASR provider actually installed (`faster-whisper-local` + Belle, or `qwen3-asr-local`).
- GPU idle window if CUDA is used.

Run (illustrative; adjust paths):

```bash
uv run python -m podcast_auto_editor transcribe "$AUDIO" \
  --provider faster-whisper-local \
  --model BELLE-2/Belle-whisper-large-v3-zh \
  --out runs/ep-real/transcript.json

uv run python -m podcast_auto_editor run "$AUDIO" \
  --transcript-json runs/ep-real/transcript.json \
  --out runs/ep-real

uv run python -m podcast_auto_editor review serve runs/ep-real/<episode-id>
```

Accept only deterministic silence automatically. Review every `speech_cut` / `retake_cut` / `backchannel_cut`. Then render. Record wall time, cut precision (word chopped or not), transcript usefulness, and gate results.

**Stop rule:** If ffmpeg or the chosen ASR is missing, write a blocker and stop. Do not install a second provider in the same session.

**Compare (optional, same file):** `auto-editor "$AUDIO"` and attach a short listen note. This is the only competitor experiment that can change the wedge.

---

## Phase 2 — One wedge (choose after Phase 1)

Pick exactly one. The others wait.

| If the fix-log says | Build | Do not build |
|---|---|---|
| Cuts are wrong or hard to judge | Review UX: transcript cue toggles the overlapping operation; previous-op navigation | New desktop app |
| Transcript is unusable | One ASR/alignment quality fix (chunking, Belle vs Qwen3, WhisperX on the same clip) | A fourth ASR brand |
| Export fails LUFS / true peak | Finish the 2026-05-18 two-pass loudnorm patch | Auphonic integration |
| Noise is the reason it is unpublishable | Optional DeepFilterNet stage, proposed-only | Default denoise; do not upload guest audio to Adobe without consent |
| Producer still finishes in Reaper/Premiere | Reaper-region EDL (or Auphonic-shaped cut list) from accepted `timeline.v1` | Full DAW |

Verified 2026-08-17 additions that do **not** jump the queue: Auphonic Editor already does per-cut review + EDL/Reaper export ([2026-04-15 blog](https://auphonic.com/blog/2026/04/15/automatic-video-cutting/)); Resound Free is 20 min / Creator $15 / Studio $60 ([resound.fm/pricing](https://www.resound.fm/pricing)); Descript’s official 25-language transcription list has no Chinese ([descript.com/pricing](https://www.descript.com/pricing)). Those facts strengthen Phase 1 (run 繁中) and the DAW-export wedge, they do not add parallel work.

---

## Phase 3 — Release process (only after Phase 1)

- Stay `0.1.x` until Phase 1 has a publish-ready export **or** a documented, reproduced failure with a fix.
- Promote `dev` → `main` for the hygiene + evidence commits, not for a vanity 1.0.
- `1.0.0` requires: one real episode green, README accurate, no "planned" flags for shipped commands, smoke.sh green.

---

## Explicitly deferred

- Lattifai k2 decode
- Packaged desktop app
- Voice cloning, publishing, cloud collaboration (already out of SDD)
- MiniMax as default LLM
- Auphonic as a backend
- Text-based Descript clone
- Provider matrix expansion

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Real audio never appears | Stop feature work. The project stays a well-tested toolbox. |
| Hygiene PR turns into a rewrite | Docs + uncommitted-patch decision only |
| Phase 1 installs every optional extra | One provider, one episode |
| Reviewer pressure to "finish 1.0" | Point at this ADR |

---

## Verification

After Phase 0: pytest + compileall + `git ls-files .omx` empty.  
After Phase 1: fix-log with numbers from the run directory, not from memory.  
After Phase 2: one failing test that names the blocker, then the smallest green.

---

## Execution handoff

This is a direction plan, not a bite-sized TDD script. When implementation starts:

1. Phase 0 as a docs PR off `dev`.
2. Phase 1 as an operator session plus a fix-log PR.
3. Phase 2 as a normal TDD feature PR.

Do not execute Phase 2 in the same PR as Phase 1.
