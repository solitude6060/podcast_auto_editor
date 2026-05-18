# PR #47 Triple Review — Codex (codex-family CLI)

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/47
- Base: `dev`
- Head: `feature/pr-x2-1-belle-real-integration` @ `5fb4d9b`
- Reviewer: `gpt-5.x` via `CODEX_HOME=$HOME/.codex-family codex exec --sandbox read-only`
- Date: 2026-05-18

## Verdict

**REQUEST CHANGES** — 1 HIGH, 2 MEDIUM, 3 LOW.

## Findings

### HIGH

**`tests/test_asr_belle_real.py:88` — `data["model"]` assertion will fail under real load**

The opt-in real test asserts `data.get("model") == "BELLE-2/Belle-whisper-large-v3-zh"`, but `transcribe_to_file()` goes through `podcast_auto_editor.asr.transcribe()`, which rebuilds the payload with only `schema_version`, `provider`, `source_media`, and `segments` (`podcast_auto_editor/asr.py:264`). The provider's own `model`, `device`, and `compute_type` fields are dropped, so this test will fail whenever `PAE_BELLE_REAL=1` reaches the assertion.

**Recommended fix**: either preserve provider metadata in `transcribe()` with focused regression coverage and update the plan/changelog for that artifact-shape behavior, or remove this assertion and use another non-public-API way to prove the model path used by the real provider.

**Triage**: Verified by reading `asr.py:264-269`. Real bug. Severity HIGH because the test would fail under the very condition it's designed to verify. Fixed via removing the model assertion (surgical, matches plan's "no public API change" rule) plus adding a wrapper-contract regression test in `tests/test_asr.py` that pins the current `transcribe()` field set. Forwarding `model`/`device`/`compute_type` is recorded in `user_todo.md` as a deferred improvement, since it expands artifact-shape contract beyond PR-X2.1's planned surface.

### MEDIUM

**`docs/walkthroughs/real-podcast-ep1.md:9` — walkthrough plural claim mismatch**

The walkthrough says real ASR, alignment, and diarization provider execution are "documented below," but the only real-provider section below is Belle ASR (`docs/walkthroughs/real-podcast-ep1.md:117`). The zh-TW standalone file makes the same plural claim (`docs/walkthroughs/real-podcast-ep1.zh-TW.md:11`) but only adds Belle ASR details.

**Recommended fix**: either add concise WhisperX and pyannote sections or links to their runbooks, or narrow the claim to PR-X2.1 Belle ASR only.

**Triage**: Real inconsistency. Fixed by narrowing the claim to Belle ASR and adding pointers to `docs/runbooks/whisperx-alignment-setup.md` and `docs/runbooks/pyannote-setup.md` for the other two.

**`user_todo.md:20` — false "synthetic-tone smoke covers the load path" claim**

The TODO says "offline synthetic-tone smoke covers the load path," but the new test skips when `PAE_BELLE_REAL_AUDIO` is absent (`tests/test_asr_belle_real.py:60`) and the plan's synthetic fallback path was not implemented despite being promised if no real fixture exists (`docs/plans/2026-05-18-pr-x2-1-belle-real-integration.md:28`).

**Recommended fix**: remove the synthetic-tone claim from `user_todo.md`, or add the fallback fixture/test path and label it as load-path-only.

**Triage**: Real plan-vs-impl mismatch. The implementer chose skip-when-missing over building a synthetic fallback (cleaner, but the plan and my user_todo.md write both promised the fallback). Fixed by rewording A2 to reflect the actual behaviour (no fallback; test simply skips).

### LOW

**`tests/test_asr_belle_real.py:43` — skip gate uses `not env.get()` instead of `!= "1"`**

The gate treats any non-empty `PAE_BELLE_REAL` value as opt-in, including `PAE_BELLE_REAL=0`, while the plan/docs describe `PAE_BELLE_REAL=1`. Sibling pyannote real tests explicitly require equality to `"1"` (`tests/test_diarization_pyannote_real.py:32`).

**Recommended fix**: change the skip condition to `os.environ.get("PAE_BELLE_REAL") != "1"`.

**Triage**: Real foot-gun (operator setting `=0` to disable would accidentally opt-in). Fixed via strict equality to match the pyannote pattern.

**`tests/test_asr_belle_real.py:103` — companion `assert True` is weak**

`test_belle_real_test_skips_cleanly_when_opted_out` is only `assert True`, so it proves module import/collection but not skip behavior.

**Triage**: **SKIPPED.** MiniMax and Gemini both defend this as a meaningful collection guard — without at least one always-passing test in the module, an import error there would silently disappear from `pytest -v` summary. Two reviewers vs one on a defensible micro-pattern → calibrate down to "intentional design", documented here.

**`CHANGELOG.md:18` and `CHANGELOG.zh-TW.md:21` — missing PR-X2.1 entry**

The changelog still describes only the PR-X2 model-id passthrough regression, not the PR-X2.1 env-gated real-load verification and walkthrough.

**Recommended fix**: add a paired English/Traditional Chinese Unreleased entry.

**Triage**: All three reviewers agree. Fixed by adding paired EN + zh-TW entries under Unreleased.

## Focus-point callouts

- Skip-by-default: mostly correct; `pytest.importorskip` correctly inside test body
- Env-var naming: defensible per plan §Open questions (boolean opt-in + path is a different pattern than path-only because Belle needs both)
- Plan-vs-diff: surgical except for the synthetic-fallback omission
- Audit trail: status entries plausible; synthetic-tone claim was inaccurate (fixed)
- False-confidence: docs disclaim character accuracy but could be more explicit about "load-path plumbing only" — addressed via one-line Notes addition
