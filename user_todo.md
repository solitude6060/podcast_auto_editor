# user_todo.md — items autopilot needs from the user

Tracks blockers that require human action so autopilot can complete the
**MVP 1.0** sweep (PR-X2.1 + version bump + stale-doc cleanup).

Date opened: 2026-05-18
Workflow: D (codex plans / Sonnet implements / triple-review / Opus 統籌)

---

## A. PR-X2.1 — real Belle-whisper-large-v3-zh integration

PR-X2 shipped the docs + model-id pin test. PR-X2.1 makes the real-load path
actually verifiable. The env-gated real test will SKIP in CI by default; it
only runs when the operator provides the prerequisites below.

| # | Item | What you do | Why | Blocking? |
|---|---|---|---|---|
| A1 | Download `BELLE-2/Belle-whisper-large-v3-zh` weights to a local path | `huggingface-cli download BELLE-2/Belle-whisper-large-v3-zh --local-dir <PATH>` (or let `faster-whisper` lazy-pull on first use; requires ~3GB and HF network) | Env-gated integration test needs a real model to load | **No** (test skipped if env unset; merge can proceed) |
| A2 | Short Chinese audio sample for the integration test | Drop a 5–10s `.wav` (mono, 16 kHz preferred) at `tests/fixtures/zh_sample.wav` (or set `PAE_BELLE_REAL_AUDIO` to your path). A real Mandarin podcast clip is preferred over TTS — the test asserts non-trivial decoded text presence, not exact transcript | Without real Chinese audio, the test only proves load + decode pipe, not language quality | **No** (test SKIPS entirely if `PAE_BELLE_REAL_AUDIO` is unset or path missing — no synthetic load-path fallback was implemented; see Codex MEDIUM) |
| A3 | Decide env var name | Confirm `PAE_BELLE_REAL=1` is OK, or pick another (existing scheme uses `PAE_WHISPERX_ALIGN_MODEL`, `PAE_LATTIFAI_ONNX_PATH`) | Consistency with prior PRs | No (planner will pick a default; you can rename before merge) |
| A4 | GPU access (optional) | Confirm whether to advertise CUDA in the runbook update, or stay CPU-only for default | Belle inference on CPU is ~5× realtime; GPU brings it well under realtime. Pure docs choice | No |

## B. MVP 1.0 release sign-off

| # | Item | What you do | Why | Blocking? |
|---|---|---|---|---|
| B1 | Approve version bump `0.1.0` → `1.0.0` in `pyproject.toml` + CHANGELOG header `Unreleased` → `1.0.0 (YYYY-MM-DD)` | Reply 確認 / 提供發布日期 | Locks the release marker; no code impact | **Yes** for release PR |
| B2 | Approve the deferred-to-1.1 list (Lattifai k2 decode, UI `k` previous-op, macOS/WSL CI) | Reply 確認, or pull anything back into 1.0 scope | Sets the 1.0 surface contract | **Yes** for release PR |
| B3 | Decide whether MVP 1.0 ships from `dev` or requires a `release/1.0` branch | Reply with preference | AGENTS.md §4 says `dev → main` via PR; either flow works | **Yes** for release PR |

## C. Things you do NOT need to action

(Recorded so I don't re-ask.)

- Triple-review reviewer keys (gemini-cli, claude-mm/MiniMax, codex) — assumed already provisioned per `feedback_code_review_protocol.md`.
- HF_TOKEN for pyannote — PR-C2 path is unchanged; if you already had it set for PR-C2 you don't need to redo it for PR-X2.1 (Belle is Apache-2.0, no auth wall).
- `qwen-asr` package install — PR-X1 already lazy-imports it; PR-X2.1 does not touch the Qwen path.

---

## Status log

- 2026-05-18 opened by autopilot. Planning PR-X2.1 in worktree (codex planner running). Audit punch list assembled.
- 2026-05-18 PR-X2.1 plan + RED test + walkthrough committed on feature/pr-x2-1-belle-real-integration; awaiting operator-provided Belle model + Chinese audio fixture per items A1/A2 above.
- Update this file inline as items resolve. Autopilot reads it before each phase.
- 2026-05-18 triple-review (Gemini 2.5-pro + MiniMax + codex-family). Codex caught the wrapper-drops-model HIGH that MiniMax+Gemini missed. 5 findings fixed; 2 LOW skipped per reviewer calibration. See docs/PR_REVIEW_2026-05-18_PR47_*.md.
