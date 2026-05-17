# X1-X4 Stage 2 series — retroactive triple review (2026-05-17)

PRs #38–#41 (Stage 2 ASR + alignment) shipped under Mini workflow with at most a single Codex review. This document captures the retroactive triple-review run + the follow-up fix landed in `pr-x-fixes/triple-review`.

## Reviewers
- Gemini 3.1 Pro Preview via `gemini --skip-trust -p ... -m gemini-3.1-pro-preview`
- MiniMax-M2.7 via Claude Code CLI against `api.minimax.io/anthropic`
- Codex (gpt-5.x) via `codex:codex-rescue` subagent

## Range
`9cfbdbe..c1339fd` on `dev`. 9 files, +683 lines.

## Triage

| # | Finding | Sources | Calibrated severity | Action |
|---|---|---|---|---|
| 1 | Qwen3-ASR provider calls `qwen_asr.transcribe(...)` — does not exist in real package; upstream API is `Qwen3ASRModel.from_pretrained(...).transcribe(...)`. Once `qwen-asr` is installed, provider always hits "no transcribe" path. | Codex (upstream-verified) + Gemini HIGH + MiniMax HIGH | **HIGH** | Fixed — rewrote provider to use class API + test stub uses fake `Qwen3ASRModel` class |
| 2 | Qwen3-ASR silently writes `segments: []` on non-list response shape | Gemini HIGH + MiniMax HIGH + Codex MED | **HIGH** | Fixed — explicit `isinstance(raw_segments, list)` check raises `ASRProviderError` |
| 3 | MockAlignmentProvider: `"hello 世界"` → 2 coarse tokens; `"hello\nworld"` (newline-only) → 11 char-split tokens. Both wrong. | MiniMax HIGH + Gemini MED + Codex MED | **HIGH** | Fixed — `text.split()` first (handles all whitespace), then per-token CJK char split. Now `"hello 世界"` → `["hello", "世", "界"]`; `"hello\nworld"` → `["hello", "world"]`. |
| 4 | No regression test for `align_to_file(transcript_segments=[])` writing valid empty artefact | MiniMax HIGH + Codex MED | LOW (intentional behaviour, just unpinned) | Added `test_align_to_file_writes_empty_segments_artefact` |
| 5 | Lattifai error message claims "phones home for quota tracking" — implementation detail unverified against upstream commit | Codex LOW + Gemini LOW | LOW | Softened to "may require authentication / usage tracking"; kept the trade-off in the operator-facing message |
| 6 | WhisperX / Lattifai provider error tests only check string match, not exception class | MiniMax MED | LOW | Added `isinstance(exc, AlignmentProviderError)` + `not isinstance(exc, ImportError)` to both tests |

## Notable

- Codex's upstream verification of the real `qwen-asr` package API turned what could have been a "MiniMax-style speculative HIGH" into a verified bug. Without that grep, the assumed API would have shipped to production and broken on first real install.
- The MockAlignmentProvider tokenization bug was independently triaged HIGH by MiniMax but MEDIUM by Gemini + Codex. Final calibrated to HIGH because both the mixed-script and newline-only paths are real-world transcript inputs (subtitle files use `\n` separators).
- Lattifai message accuracy: three different reviewers reached three different verdicts (MiniMax: PASS, Gemini: rigid claim risk, Codex: unverifiable detail). Softened in code to remove the unverifiable specifics while keeping the trade-off explicit.

## Verification
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider` → 266 passed (was 261 on `dev` pre-fix; +5 net regression tests)
- `compileall` OK, `smoke` 266 passed, `.omx` empty
- No new dependencies; lazy-import discipline preserved
