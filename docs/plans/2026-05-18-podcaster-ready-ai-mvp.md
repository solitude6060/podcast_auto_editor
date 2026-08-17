# Podcaster-ready AI MVP autopilot plan

Date: 2026-05-18
Mode: `$autopilot` (`$ralplan -> $ralph -> $code-review`)
Context snapshot: `.omx/context/podcaster-ready-ai-mvp-20260518T150022Z.md`

## zh-TW summary

本計畫把「可以開始做 podcast」拆成兩層交付：

1. **本輪必交付**：修正真實音檔輸出的 loudness / quality metadata / report / dashboard 基礎，讓使用者能判斷 MP3 是否 publish-ready，且不用讀 JSON 審靜音剪輯。
2. **條件式交付**：ASR、真實 LLM、pyannote、MiniMax fallback 都需要本機模型、服務或憑證可用；本輪要把 CLI 診斷、錯誤訊息、runbook 和 fallback 邊界做好。若環境可用，直接跑真實 transcript + AI draft；若不可用，產生明確 blocker，不把密鑰或媒體寫進 repo。

MiniMax key must remain ephemeral. Do not write it to repo files, `.omx`, docs, command history artifacts, or logs.

## Goal

Make the existing local-first MVP usable on a real podcast recording:

- produce publish-ready or clearly failed audio exports with measured quality details;
- preserve review-safe timeline / recipe / preview artifacts;
- expose quality and review decisions in producer-facing CLI/dashboard outputs;
- enable real transcript + AI draft when local/explicit fallback models are available;
- keep speech-changing edits proposed-only until review.

## RALPLAN-DR

### Principles

- Local-first by default; cloud fallback only when explicitly selected.
- No hidden destructive edits: speech changes remain review-gated.
- Publishability requires measured audio evidence, not optimistic file existence.
- Keep private media, generated runs, credentials, and `.omx` out of git.
- Prefer small verified increments over broad AI automation.

### Decision drivers

1. The current real run is blocked by `podcast-stereo` loudness and misleading report output.
2. Real AI value depends on real transcript quality; stub transcript makes AI draft meaningless.
3. Optional ML dependencies are absent in the current core env, so production paths need diagnostics and graceful blockers.

### Options considered

- **Option A: Quality/report/dashboard first, then model-gated AI. Chosen.**
  - Pros: fixes the immediate publish blocker, avoids unsafe cloud/credential behavior, creates trustworthy evidence for every later AI path.
  - Cons: does not magically make ASR/diarization work if local dependencies are absent.
- **Option B: Install/run all AI dependencies first. Rejected.**
  - Pros: fastest route to impressive demos if the environment is ready.
  - Cons: may trigger large downloads, network access, gated licenses, GPU contention, and credential handling before the core export gate is trustworthy.
- **Option C: Add MiniMax as the primary LLM. Rejected.**
  - Pros: avoids local endpoint availability issues.
  - Cons: violates local-first default and would put a credentialed external service on the critical path. Keep MiniMax explicit fallback only.

## Scope

### Must implement in this autopilot cycle

1. **Loudness/export robustness**
   - Add regression coverage using real FFmpeg fixture behavior where possible.
   - Make rendered podcast MP3 profiles land within configured LUFS tolerance for the observed real-world near-miss.
   - Preserve true peak and clipping gates.
   - Avoid leaving ambiguous partial-success metadata when a later profile fails.

2. **Quality metadata/report fix**
   - Persist per-profile quality gate reports before raising a quality failure when feasible.
   - Ensure CLI markdown/JSON report and HTML report show failed profile, failed check names, targets, actual values, and warnings.
   - Quickstart real-audio fallback must clearly identify that inspection artifacts were produced but publish exports are not ready.

3. **Producer dashboard baseline**
   - Expose per-operation before/after and removed-preview links in the local dashboard.
   - Keep accept/reject decision flow localhost-only and JSON-backed.
   - Add keyboard or button path tests if currently missing.

4. **AI environment and real-run orchestration**
   - Add or improve a command/runbook path that reports whether qwen/faster-whisper/whisper.cpp/pyannote/local LLM/MiniMax fallback are available without leaking credentials.
   - If local ASR dependencies are unavailable, fail with an actionable message and do not write fake "real" transcripts.
   - If a real transcript is available, `ai draft` should call the configured local/OpenAI-compatible endpoint unless `--dry-prompt`/`--no-net` is used.
   - MiniMax remains an explicit fallback path only; credentials are read from env and never persisted.

### Deferred unless dependencies are already available

- Installing `qwen-asr`, `faster-whisper`, `pyannote.audio`, WhisperX, or large model weights.
- Long-running GPU diarization/transcription benchmarks.
- Automatic speech/retake deletion. Detection can propose operations, but render safety must require review provenance.

## Touchpoints

- `podcast_auto_editor/media.py`
- `podcast_auto_editor/pipeline.py`
- `podcast_auto_editor/quality.py`
- `podcast_auto_editor/exports.py`
- `podcast_auto_editor/cli.py`
- `podcast_auto_editor/html_report.py`
- `podcast_auto_editor/local_review_server.py`
- `podcast_auto_editor/asr.py`
- `podcast_auto_editor/ai_drafts.py`
- `podcast_auto_editor/ai_doctor.py`
- `podcast_auto_editor/ai_models.py`
- `podcast_auto_editor/diarization.py`
- `tests/test_exports.py`
- `tests/test_acceptance_ffmpeg.py`
- `tests/test_cli.py`
- `tests/test_html_report.py`
- `tests/test_local_review_server.py`
- `tests/test_ai_drafts.py`
- `tests/test_asr*.py`
- `tests/test_diarization*.py`

## Acceptance criteria

- Real or representative FFmpeg fixture export passes all configured quality checks for `archive-wav`, `podcast-stereo`, and `podcast-mono`.
- A quality failure report names the exact export profile and failed check, including target and actual values.
- `report --format markdown` no longer prints `Quality gate: not measured` when profile quality data exists.
- Quickstart real-audio fallback preserves inspection artifacts and clearly marks publish output as not ready.
- Dashboard exposes operation preview refs and decision controls without requiring JSON inspection.
- ASR/LLM/diarization paths either run with real dependencies or return actionable setup errors without writing misleading artifacts.
- Full verification passes:
  - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider`
  - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests`
  - `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor ./scripts/smoke.sh`
  - `git ls-files .omx` has no output.

## Risks

- One-pass FFmpeg `loudnorm` can miss target tolerance on real audio; a two-pass or measured correction may be required.
- Qwen3-ASR single-segment limit means the 27-minute sample needs chunking or a different provider.
- Local LLM endpoint availability is transient; live AI tests must be opt-in or skipped cleanly.
- MiniMax fallback is credentialed and networked; never make it default.
- pyannote model is gated and may need license acceptance plus token.

