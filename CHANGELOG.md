# Changelog

Traditional Chinese version: [`CHANGELOG.zh-TW.md`](CHANGELOG.zh-TW.md)

All notable changes to this project should be documented here.

## Unreleased

### Added
- Podcaster-ready export hardening: audio rendering now uses measured two-pass loudnorm, lossy podcast exports retry with additional true-peak headroom when needed, and run reports surface per-export quality target/actual details plus the failed profile.
- Local-first podcast auto-editor MVP with reversible timeline edits, previews, diff/recovery artifacts, transcript/subtitle/chapter outputs, export profiles, review sessions, and static HTML reports.
- CI workflow that mirrors local uv pytest and compileall checks.
- AI drafting support with `podcast_auto_editor ai draft`, producing `ai/ai-draft.v1.json` from timeline + transcript, with `--dry-prompt`/`--dry-run` offline mode.
- AI explainability support for `podcast_auto_editor explain --with-ai`, including `ai_explanation` payload and safe `--dry-prompt` behavior.
- Local review dashboard concentration updates: `review serve` now includes AI draft path and artifact/status context in both API and HTML output.
- Docker local AI stack E2E check script: `scripts/e2e-docker-ai-stack.sh` and focused e2e script coverage.
- `podcast-auto-editor recipe export/apply` — bundle a run directory into a portable `recipe.v1.json` and replay it against the same source media. Source media sha256 is verified on apply; pass `--allow-media-drift` to override. The recipe embeds the accepted timeline, config snapshot, and optional AI draft so downstream tools / collaborators can reproduce the edit deterministically.
- New ASR provider `qwen3-asr-local` for [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) (Apache-2.0). Lazy-imports `qwen-asr` so the base install stays slim. Surfaces a clear `ASRProviderError` when the optional dep is missing or when the installed package does not expose the expected `transcribe` entry point. Long audio (>20 min) chunking is the caller's responsibility per the model card.
- Document that `faster-whisper-local --model BELLE-2/Belle-whisper-large-v3-zh` is a drop-in Chinese ASR upgrade (Apache-2.0). Reported CER improvement vs vanilla `whisper-large-v3` is -24~-66% across AISHELL / WenetSpeech / HKUST. Added regression test pinning the HuggingFace model id passes through to the underlying WhisperModel constructor unchanged. See `docs/research/2026-05-17-chinese-asr-models.md` for the broader Chinese ASR landscape.
- PR-X2.1: env-gated real-load integration test for `BELLE-2/Belle-whisper-large-v3-zh` through the `faster-whisper-local` ASR provider, plus an operator walkthrough section in `docs/walkthroughs/real-podcast-ep1.md`. Test skips by default; run with `PAE_BELLE_REAL=1 PAE_BELLE_REAL_AUDIO=<path>` to exercise the real load path. No public CLI surface change.
- `podcast-auto-editor quickstart [--out <dir>] [--episode-id demo]` — one-shot demo: generates the demo fixtures, runs the pipeline against the synthetic silence sample, prints the resulting run directory plus the suggested `report` / `review serve` follow-ups. Fails fast with a clear error if `ffmpeg` is missing.
- `scripts/install.sh` — Linux + uv installer. Idempotent (running twice is safe), exits clearly when `uv` is not on `PATH` (pointing at the upstream install docs), and skips demo fixture generation when `ffmpeg` is unavailable. macOS / WSL paths remain documented-but-unverified.
- New operation type `backchannel_cut` for short affirmative interjections ("right", "mhm", "對對對"). Behaves like `speech_cut` from a render-safety standpoint: always proposed, never auto-accepted, requires manual review with preview/diff/recovery artefacts. `detect_backchannel_candidates(transcript_segments, speaker_aggression=...)` is the producer; `detect_speech_cleanup_candidates` gained the same optional `speaker_aggression={"spk0": "off"}` argument so a host's filler style can be preserved while a guest's is still flagged.
- `ai draft --speaker-segments speaker_segments.v1.json --speaker-label spk0=Host --speaker-label spk1=Guest` — when speaker_segments are supplied, the AI draft prompt includes a `Speakers:` block so the LLM can attribute chapters to a specific speaker. Generated chapters carry an optional `speaker_id` field (null when the LLM doesn't attribute). Backward compatible: existing runs without speaker_segments produce the same prompt and output shape as before.
- `podcast-auto-editor diarize INPUT --provider mock|pyannote --out speaker_segments.v1.json --config X.json` — generates a `speaker_segments.v1.json` artefact for downstream per-speaker AI draft attribution and per-speaker filler detection. The `mock` provider reads a config JSON and ships offline (no network, no HF token); the `pyannote` adapter is wired with a lazy import and currently raises a clear `DiarizationProviderError` distinguishing "dependency missing" from "integration deferred to PR-C2". `transcript.v1` cues may carry an optional `speaker_id` field that is preserved through validation.
- `ai draft` / `explain --with-ai` read `MINIMAX_API_KEY` from the environment for explicitly selected MiniMax-compatible endpoints without persisting the credential, and `ai doctor` now reports optional ASR/diarization Python packages.
- Review dashboard now exposes a per-operation detail endpoint at `GET /api/operation/<id>` returning the same canonical payload shape as the `next` field from `/api/status` (operation_id, type, state, risk, confidence, source, detector, reason_code, evidence_text, required_review, preview_ref, removed_ref, decision_commands). Filter parameter on `GET /api/status?filter=<type>` narrows the `next` field so producers can sweep silence-cuts first, then retake-cuts. Browser keyboard nav: `a` accept, `r` reject, `u` undo, `j` advance to the next pending operation. `k` currently mirrors `j` as a forward alias; true previous-operation navigation is a follow-up. Keyboard shortcuts are suppressed when typing in the reviewer or note inputs. The `/api/operation/<id>` path guard rejects percent-encoded traversal variants (`%2e%2e`, `%2F…`), control characters, and `.`/`..` segments before lookup.

### Changed
- README comparison table now includes WyattBlue `auto-editor`, marks `recipe.v1` as implemented, and states that denoise is not shipped. SDD verification cites the current collect count. `user_todo.md` 1.0 sign-off (B1–B3) is superseded by `docs/plans/2026-08-17-adjustment-and-next.md`. The pyannote adapter runs the real pipeline when optional deps, `HF_TOKEN`, and the model license are present; the older Added bullet that said integration was deferred is historical.
- Pending public release; keep entries grouped under Added/Changed/Fixed/Security.

### Fixed
- Pyannote pipeline load skips the optional CUDA `.to` move when the pipeline object has no `.to`, so test fakes and CPU-only objects no longer crash on CUDA hosts.
- Added `--dry-run` alias path handling for `podcast_auto_editor ai draft` (mapped to no-network draft-mode behavior).
- Dashboard context now consistently persists `ai_draft` path/link data for UI and JSON clients when present.
