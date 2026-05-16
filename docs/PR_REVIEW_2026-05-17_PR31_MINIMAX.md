# PR #31 — MiniMax code review (via claude-mm)

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/31
- Base: `dev` → Head: `pr-c/diarization-cli`
- Head SHA: `a1d4cf0`
- Review date: 2026-05-17
- Reviewer: `MiniMax-M2.7` via Claude Code CLI against `api.minimax.io/anthropic`
- Verdict: **REQUEST CHANGES**

## Findings

### CRITICAL (calibrated MEDIUM per Gemini LOW + Codex MEDIUM)
- **`diarization.py:67`** — `start < 0` not validated. MiniMax calibrated CRITICAL citing data-integrity risk. Gemini calibrated LOW (acceptable unless downstream requires it); Codex calibrated MEDIUM (rolls into broader finite-number / bool / negative gap). **Final calibration: MEDIUM** — real input-validation gap but unlikely to be triggered by real pyannote output. Fix is cheap and is grouped with the other finite-number checks. **Disposition: Fixed in fix round.**

### HIGH (calibrated LOW per Gemini + Codex disagreement)
- **`diarization.py:55-78`** — No monotonicity / overlap validation across segments. MiniMax calibrated HIGH. Gemini explicitly said "Overlaps SHOULD be allowed for diarization, so lack of overlap checking is correct." Codex said "intentional design choice because real diarization can produce overlapping speaker turns and the PR does not declare an ordering invariant." Two reviewers against one + the codebase has no SPEC requiring this invariant for speaker_segments. **Final calibration: LOW.** **Disposition: Skipped** — not a bug; the artefact may legitimately carry overlapping speaker turns.

### MEDIUM
- **`tests/test_diarization.py`** — No `start < 0` test. **Disposition: Folded into Fix #1** — `test_normalize_speaker_segments_rejects_negative_start` added.
- **`tests/test_diarization.py`** — No test for empty segments through `diarize_to_file`. **Disposition: Folded** — regression guard test added.
- **`diarization.py:72` `dict(raw_seg)` shallow copy semantics** — Documented for awareness; no nested-mutable fields are expected in `speaker_segments.v1`. No change needed.

### LOW
- **`tests/test_diarization.py` pyannote dual-path docstring** — Add a docstring noting that both "dependency missing" and "integration deferred" paths produce a passing test. No code change. Skipped (test docstring already mentions both cases).
- **CLI / regression pin / schema discipline / `Co-authored-by`:** all confirmed clean.

## Focus-point summary
All addressed in the findings above. Final action set: fix start < 0 + bool + NaN/inf, fix mock JSON error wrap, skip monotonicity/overlap, add empty-segments regression test, add README docs.
