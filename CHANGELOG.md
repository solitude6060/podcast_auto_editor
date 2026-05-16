# Changelog

Traditional Chinese version: [`CHANGELOG.zh-TW.md`](CHANGELOG.zh-TW.md)

All notable changes to this project should be documented here.

## Unreleased

### Added
- Local-first podcast auto-editor MVP with reversible timeline edits, previews, diff/recovery artifacts, transcript/subtitle/chapter outputs, export profiles, review sessions, and static HTML reports.
- CI workflow that mirrors local uv pytest and compileall checks.
- AI drafting support with `podcast_auto_editor ai draft`, producing `ai/ai-draft.v1.json` from timeline + transcript, with `--dry-prompt`/`--dry-run` offline mode.
- AI explainability support for `podcast_auto_editor explain --with-ai`, including `ai_explanation` payload and safe `--dry-prompt` behavior.
- Local review dashboard concentration updates: `review serve` now includes AI draft path and artifact/status context in both API and HTML output.
- Docker local AI stack E2E check script: `scripts/e2e-docker-ai-stack.sh` and focused e2e script coverage.
- `podcast-auto-editor recipe export/apply` — bundle a run directory into a portable `recipe.v1.json` and replay it against the same source media. Source media sha256 is verified on apply; pass `--allow-media-drift` to override. The recipe embeds the accepted timeline, config snapshot, and optional AI draft so downstream tools / collaborators can reproduce the edit deterministically.
- `ai draft --speaker-segments speaker_segments.v1.json --speaker-label spk0=Host --speaker-label spk1=Guest` — when speaker_segments are supplied, the AI draft prompt includes a `Speakers:` block so the LLM can attribute chapters to a specific speaker. Generated chapters carry an optional `speaker_id` field (null when the LLM doesn't attribute). Backward compatible: existing runs without speaker_segments produce the same prompt and output shape as before.
- `podcast-auto-editor diarize INPUT --provider mock|pyannote --out speaker_segments.v1.json --config X.json` — generates a `speaker_segments.v1.json` artefact for downstream per-speaker AI draft attribution and per-speaker filler detection. The `mock` provider reads a config JSON and ships offline (no network, no HF token); the `pyannote` adapter is wired with a lazy import and currently raises a clear `DiarizationProviderError` distinguishing "dependency missing" from "integration deferred to PR-C2". `transcript.v1` cues may carry an optional `speaker_id` field that is preserved through validation.
- Review dashboard now exposes a per-operation detail endpoint at `GET /api/operation/<id>` returning the same canonical payload shape as the `next` field from `/api/status` (operation_id, type, state, risk, confidence, source, detector, reason_code, evidence_text, required_review, preview_ref, removed_ref, decision_commands). Filter parameter on `GET /api/status?filter=<type>` narrows the `next` field so producers can sweep silence-cuts first, then retake-cuts. Browser keyboard nav: `a` accept, `r` reject, `u` undo, `j` advance to the next pending operation. `k` currently mirrors `j` as a forward alias; true previous-operation navigation is a follow-up. Keyboard shortcuts are suppressed when typing in the reviewer or note inputs. The `/api/operation/<id>` path guard rejects percent-encoded traversal variants (`%2e%2e`, `%2F…`), control characters, and `.`/`..` segments before lookup.

### Changed
- Pending public release; keep entries grouped under Added/Changed/Fixed/Security.

### Fixed
- Added `--dry-run` alias path handling for `podcast_auto_editor ai draft` (mapped to no-network draft-mode behavior).
- Dashboard context now consistently persists `ai_draft` path/link data for UI and JSON clients when present.
