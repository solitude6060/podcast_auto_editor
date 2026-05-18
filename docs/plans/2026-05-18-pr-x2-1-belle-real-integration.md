# PR-X2.1 Belle Real Integration Plan

## Goal
Prove that `faster-whisper-local --model BELLE-2/Belle-whisper-large-v3-zh` is not only a model-id passthrough but a real local integration path: a gated test should load the Belle faster-whisper model, transcribe a short Chinese sample, and leave operators with a documented one-line command for Chinese ASR without changing the public provider API.

## Non-goals
- No public CLI surface change.
- No auto-detect-Chinese language gate.
- No model download automation.
- No fine-tuning instructions.

## Surface
- `tests/test_asr_belle_real.py` — add the gated real-load integration test for Belle through `faster-whisper-local`.
- `tests/fixtures/` — use an existing short Chinese audio fixture if present; otherwise add a synthetic fallback fixture only as a load-path smoke input.
- `docs/walkthroughs/real-podcast-ep1.md` — add a "Chinese ASR via Belle" operator section, creating the walkthrough path if it is still absent at implementation time.
- `docs/walkthroughs/real-podcast-ep1.zh-TW.md` — add the same operator path in Traditional Chinese if the walkthrough exists or is created.
- `user_todo.md` — mirror user-blocked items such as model availability and a real Chinese audio sample.

## Dependencies
- `faster-whisper` must be installed in the local environment; the core package remains dependency-light and the normal test suite must pass without it.
- `BELLE-2/Belle-whisper-large-v3-zh` must be available to `faster_whisper.WhisperModel`, either through the Hugging Face cache or a compatible local model path accepted by faster-whisper.
- The real-load test is gated by `PAE_BELLE_REAL=1` and skipped by default in CI/offline runs.
- A short Chinese audio sample of about 10 seconds is required to validate decoding quality; if no real fixture exists, the synthetic fallback is explicitly labelled as load-path-only and not evidence of Chinese decoding.
- GPU is optional for the plan, but a CUDA device with `compute_type=float16` is the recommended operator path for the large Belle model; CPU fallback can use a slower compute type only when explicitly selected.

## Open questions + decision on each
- Env var name: PR-X3.1 could not be inspected because `docs/plans/2026-05-18-pr-x3-1-whisperx-chinese-alignment.md` is absent in this worktree. Decision: use `PAE_BELLE_REAL=1`, matching the project-specific prefix and the requested naming scheme.
- Sample-fixture source: `tests/fixtures/` is absent in this worktree, so there is no existing Chinese audio fixture to reuse. Decision: plan a real ~10s Chinese fixture as the preferred path; if unavailable during implementation, create a synthetic tone+silence fallback labelled "synthetic -- does not exercise real Chinese decoding" and add a `user_todo.md` item for the user to supply real audio.
- CLI preset vs explicit model: `--asr-preset chinese-belle` would add new public surface for one model choice, while `--model BELLE-2/Belle-whisper-large-v3-zh` already matches the existing provider contract and PR-X2 passthrough test. Decision: recommend the explicit `--model` one-liner and do not add a preset.
- CLI smoke test via `faster-whisper-local --model`: include a manual/operator smoke command in the walkthrough, but keep the automated test at the provider level so it can assert transcript shape and skip cleanly behind `PAE_BELLE_REAL=1`.
- Reference plan structure: both requested reference files, `docs/plans/2026-05-18-pr-x3-1-whisperx-chinese-alignment.md` and `docs/plans/2026-05-18-pr-x4-1-lattifai-onnx-air-gap.md`, are absent. Decision: keep the required section ordering from this task and follow the terse repo plan style used by existing `docs/plans/*.md` files.

## TDD outline
RED:
- Add `tests/test_asr_belle_real.py` with one skipped-by-default integration test.
- The first failing assertion under `PAE_BELLE_REAL=1` should call `cli.transcribe_to_file(..., provider_name="faster-whisper-local", model="BELLE-2/Belle-whisper-large-v3-zh", device=<env/default>, compute_type=<env/default>)` against the short fixture and require a `transcript.v1` payload with provider `faster-whisper-local`, model `BELLE-2/Belle-whisper-large-v3-zh`, and at least one non-empty segment.
- If only the synthetic fallback fixture is present, the test must still verify load/transcribe plumbing but must not assert Chinese text quality.

GREEN:
- Add only the fixture/doc support needed for the gated test to run; do not change `FasterWhisperLocalProvider` public API because PR-X2 already verifies Belle model-id passthrough.
- Ensure the default test run reports the Belle test as skipped unless `PAE_BELLE_REAL=1` is set.
- Document the exact operator one-liner in the walkthrough using the existing `transcribe --provider faster-whisper-local --model BELLE-2/Belle-whisper-large-v3-zh` pattern.

REFACTOR:
- Keep the new integration test isolated from `tests/test_asr.py` so the existing PR-X2 passthrough coverage is not duplicated.
- Keep fixture naming explicit enough to distinguish real Chinese decoding evidence from synthetic load-path evidence.
- Avoid helper abstractions unless another real-model gated test already establishes a shared pattern.

## Test matrix
- Offline-no-model: run the normal suite with no `PAE_BELLE_REAL`; expected result is a skipped Belle real-load test and no optional dependency requirement.
- Offline-with-real-model-env-gated: run `PAE_BELLE_REAL=1` with `faster-whisper` installed and Belle available locally or in cache; expected result is a transcript with non-empty segments from `faster-whisper-local`.
- Model-id passthrough already covered by PR-X2: keep `tests/test_asr.py::test_faster_whisper_provider_accepts_belle_whisper_zh_drop_in` as the passthrough regression and do not duplicate it in PR-X2.1.

## Risk + rollback
- Risk: the Belle model may require large downloads, GPU memory, or faster-whisper conversion support that is unavailable in default CI. Mitigation: gate with `PAE_BELLE_REAL=1`, skip by default, and document local prerequisites.
- Risk: a synthetic audio fallback can prove model loading but not Chinese decoding. Mitigation: label it clearly and keep a user-blocked TODO for a real Chinese fixture before treating PR-X2.1 as decoding-quality evidence.
- Risk: adding a preset would expand CLI support burden for a single model id. Mitigation: use the existing explicit `--model` flow and make rollback a docs/test removal only.
- Rollback: remove `tests/test_asr_belle_real.py`, the Belle walkthrough section, and any PR-X2.1 fixture additions; no provider API rollback should be needed.

## Branch & PR plan
- Branch from `dev`: `feature/pr-x2-1-belle-real-integration`.
- Commit 1: add the gated Belle real-load integration test and fixture handling.
- Commit 2: add the English and Traditional Chinese walkthrough updates plus `user_todo.md` entries for user-blocked assets.
- Verification before PR: run the normal uv pytest/compileall gate without `PAE_BELLE_REAL`, then run the gated Belle test only in an environment with the model and sample fixture available.
- Triple-review trigger: request triple review before merging into `dev` because this is a real optional-model integration with environment-gated behavior and operator documentation.

### User-blocked
- Model download or local cache: the user must make `BELLE-2/Belle-whisper-large-v3-zh` available to faster-whisper before the gated test can pass.
- GPU optional: the user should provide a CUDA-capable environment for practical runtime, though CPU may be acceptable for a slow manual verification path.
- Sample Chinese audio file: the user should supply a real ~10s Chinese speech fixture; otherwise PR-X2.1 can only prove model loading with a synthetic load-path fallback, not real Chinese decoding.
