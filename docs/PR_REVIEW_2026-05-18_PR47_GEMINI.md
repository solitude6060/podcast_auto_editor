# PR #47 Triple Review — Gemini

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/47
- Base: `dev`
- Head: `feature/pr-x2-1-belle-real-integration` @ `5fb4d9b`
- Reviewer: `gemini-2.5-pro` via `gemini --skip-trust -p ... -m gemini-2.5-pro`
- Date: 2026-05-18

> **Fallback note**: `gemini-3.1-pro-preview` returned RESOURCE_EXHAUSTED (model
> capacity). Retried with `gemini-2.5-pro` per skill troubleshooting. The model
> produced two passes that disagree on verdict (one APPROVE, one REQUEST
> CHANGES); both are archived below since their findings are complementary.

## Pass 1 — Verdict: APPROVE

### MEDIUM
- **Env-var naming inconsistency** (`tests/test_asr_belle_real.py:28`): `PAE_BELLE_REAL=1` + `PAE_BELLE_REAL_AUDIO` differs from sibling pattern (`PAE_WHISPERX_ALIGN_MODEL`, `PAE_LATTIFAI_ONNX_PATH`). Recommends collapsing to a single env var.

  **Triage**: **SKIPPED** (same calibration as MiniMax's MEDIUM — plan §Open questions defends the divergence).

### LOW
- **Missing `CHANGELOG.md` entry**: no Unreleased entry for PR-X2.1.

  **Triage**: Fixed.

### Focus-point callouts
- Skip-by-default correctness: OK
- Companion test: defended as meaningful guard (aligns with MiniMax)
- Assertion strength: noted that `data["model"]` assertion is appropriate (but did NOT verify it against `asr.py:transcribe()` — this is where Pass 1 missed the HIGH bug Codex caught)
- Walkthrough doc consistency: verified
- Plan-vs-diff: aligned

## Pass 2 — Verdict: REQUEST CHANGES

### MEDIUM
- **Missing synthetic fixture fallback** (`user_todo.md:20`, `tests/test_asr_belle_real.py:61`): Plan §28 promised a synthetic tone+silence fallback if no real Chinese fixture exists. Implementer chose `pytest.skip` instead. `user_todo.md` claims "offline synthetic-tone smoke covers the load path" which is factually incorrect.

  **Triage**: Same as Codex MEDIUM (#2). Fixed by rewording `user_todo.md` A2 to match reality.

### LOW
- **`PAE_BELLE_REAL=0` truthy bug** (`tests/test_asr_belle_real.py:44`): `not os.environ.get("PAE_BELLE_REAL")` returns `False` for the string `"0"`, so explicitly disabling via `=0` would unexpectedly opt-in.

  **Triage**: Same as Codex LOW (#5). Fixed by changing to `os.environ.get("PAE_BELLE_REAL") != "1"`.

### Focus-point callouts
- Pass 2 still asserts: "The test correctly asserts `data.get("model") == "BELLE-2/Belle-whisper-large-v3-zh"`. Combined with the non-empty text check, this proves the correct model ID was routed to the provider..."

  **⚠ Reviewer hallucination — this claim is factually wrong**: Codex verified via reading `asr.py:264-269` that `transcribe()` rebuilds the payload without `model`/`device`/`compute_type`, so the assertion would fail under real load. Gemini did not verify this collaborator function; MiniMax also did not verify. Codex's cross-reference saved the test from a silent broken-when-actually-run state.

## Net new findings (vs MiniMax + Codex)

- The synthetic-fallback mismatch was independently raised by both Codex (MEDIUM #2) and Gemini Pass 2. Cross-verification strengthens severity.
- The `PAE_BELLE_REAL=0` truthy bug was independently raised by both Codex (LOW #5) and Gemini Pass 2. Cross-verification strengthens severity.
- Gemini did NOT catch the wrapper-drop bug (Pass 2 actively defended the broken assertion as correct). Documented in calibration notes as a reviewer-blind-spot when a reviewer reads the test in isolation without grepping the wrapper.

## Calibration note

Two-pass mode (preview model exhausted → fallback model retry) produced two reviews that should ideally agree. Disagreement here is informative: Pass 1's APPROVE is consistent with "the code is internally consistent and matches the plan"; Pass 2's REQUEST CHANGES is consistent with "the plan promised a synthetic fallback that wasn't built". Both are correct readings at different abstractions; the plan-deviation reading wins because plan-conformance is the contract.
