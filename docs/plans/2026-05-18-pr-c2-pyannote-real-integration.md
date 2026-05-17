# PR-C2 Pyannote 3.1 Real Diarization Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:test-driven-development` for the implementation pass. This plan is the handoff contract only; do not implement from this branch.

**Goal:** Replace the deferred `PyannoteDiarizationProvider` stub with real `pyannote/speaker-diarization-3.1` diarization while preserving the existing `speaker_segments.v1` artifact contract and slim default install.

**Architecture:** Keep `podcast_auto_editor.diarization` as the provider boundary. Load `pyannote.audio` lazily inside the pyannote provider path, construct the pipeline on first use per provider instance, normalize pyannote output through the existing segment validator, and report dependency/auth/license failures as `DiarizationProviderError`.

**Tech Stack:** Python stdlib provider boundary, optional `pyannote.audio` 3.x, PyTorch, Hugging Face gated model `pyannote/speaker-diarization-3.1`, pytest with real-model tests gated by `PAE_PYANNOTE_REAL=1` and `HF_TOKEN`.

---

## 1. Why

The current `PyannoteDiarizationProvider` in `podcast_auto_editor/diarization.py` is a deliberate PR-C stub: it lazy-imports `pyannote.audio`, then raises `DiarizationProviderError` saying real model integration is deferred. That let the CLI, mock provider, and `speaker_segments.v1` schema land without a Hugging Face token or real recording.

PR-C2 unblocks actual speaker attribution for interview podcasts. Downstream PR-D and PR-E depend on real `speaker_segments.v1` output so AI drafts can cite speakers and future speech-cleanup heuristics can make per-speaker decisions. The user's 2026-05-17 decision was to proceed with PR-C2 and provide `HF_TOKEN` out-of-band; the implementation must therefore consume an existing token from the environment or pyannote/Hugging Face's own local token lookup without prompting, writing, storing, or logging credentials.

The research note `docs/research/2026-05-17-chinese-asr-models.md` identifies `pyannote/speaker-diarization-3.1` as the current OSS standard for diarization, gated but acceptable, with Chinese-relevant training data and lower integration risk than switching to NeMo or an all-in-one WhisperX pipeline.

## 2. Constraints

- `HF_TOKEN` is env-only for repository code. The implementation may read `os.environ["HF_TOKEN"]` or `os.environ.get("HF_TOKEN")`; it must not prompt, persist, print, redact-and-store, or write a token into any repo artifact.
- The pyannote pipeline must also be allowed to use pyannote/Hugging Face's own `~/.huggingface/token` lookup when no `HF_TOKEN` env var is passed, but project code must not create or mutate that file.
- `pyannote.audio` stays optional under a `diarize-pyannote` extra/dependency group. A core install must still import `podcast_auto_editor.diarization` and run mock-provider tests without the heavy ML stack.
- Import `pyannote.audio` only inside `PyannoteDiarizationProvider.diarize()` or an instance helper called from `diarize()`. No module-top imports of `pyannote`, `torch`, or Hugging Face SDKs.
- Missing dependency, missing token, and missing license acceptance must raise `DiarizationProviderError` with clear user action. The auth/license message must point to: accept the license at `https://huggingface.co/pyannote/speaker-diarization-3.1`, set `HF_TOKEN`, and re-run.
- Data shape and validation failures after a provider succeeds remain `DiarizationError`; provider configuration/auth/dependency/runtime availability failures remain `DiarizationProviderError`.
- Do not leak `HF_TOKEN` into logs, exception messages, JSON artifacts, pytest assertion output, runbooks, or docs examples.
- Network/model download is an explicit operator concern. Document the one-time model download size/risk and a pre-cache command using `hf download pyannote/speaker-diarization-3.1`; do not silently add always-online behavior beyond pyannote's normal first-load cache.

## 3. Deliverables

- Modify `podcast_auto_editor/diarization.py`.
  Replace `PyannoteDiarizationProvider.diarize()` with the real pyannote call. Use `Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=os.environ.get("HF_TOKEN"))`, with the import inside the method/helper. Cache the constructed pipeline on the provider instance after the first successful load. Call the pipeline on `audio_path`, iterate over `annotation.itertracks(yield_label=True)`, and normalize to the existing schema: `{"start": float(turn.start), "end": float(turn.end), "speaker_id": str(label), "confidence": 0.0}` unless pyannote exposes a reliable score in the returned object. Pass the raw list through `normalize_speaker_segments()` before returning.
- Modify `pyproject.toml`.
  Add an opt-in `diarize-pyannote` optional dependency group containing `pyannote.audio` and `torch`. Document the CPU default and CUDA choice in comments/docs rather than forcing CUDA-specific wheels into the default install. Keep the base dependency set unchanged.
- Add `docs/runbooks/pyannote-setup.md`.
  Provide a step-by-step operator runbook: create or sign in to Hugging Face, accept the gated model license at the model page, generate a token, export `HF_TOKEN`, optionally run `hf download pyannote/speaker-diarization-3.1` to pre-cache the model, install the extra, and run a short `diarize` smoke command. Include a warning that first download may be large and network-bound.
- Add `tests/test_diarization_pyannote_real.py`.
  New env-gated tests. Skip real-model tests unless both `PAE_PYANNOTE_REAL=1` and `HF_TOKEN` are set. Cover a known short 2-speaker clip expecting exactly two distinct speaker labels, a 1-speaker monologue expecting one distinct speaker label, missing-token error message, missing-dependency error message, schema preservation, timestamp invariants, and token non-leakage. Test fixtures should be small local audio files or generated deterministic fixtures; do not require downloading test audio from the network during pytest.
- Modify `tests/test_diarization.py`.
  Update `test_pyannote_provider_raises_clear_error_when_called` only if the stub-era error semantics change enough that the old assertion no longer describes the provider. Keep the dependency-missing path covered without requiring `pyannote.audio` in the core test environment.

## 4. TDD Test List

- `test_pyannote_provider_raises_clear_error_when_dependency_missing`: monkeypatch import failure for `pyannote.audio`; assert `DiarizationProviderError` names `diarize-pyannote` install instructions and does not mention any token value.
- `test_pyannote_provider_raises_clear_error_when_hf_token_missing`: simulate installed pyannote with no `HF_TOKEN` and no usable local token; assert the error tells the user to set `HF_TOKEN` and re-run.
- `test_pyannote_provider_raises_clear_error_when_license_not_accepted`: simulate `Pipeline.from_pretrained()` raising the gated-repo/license failure, if distinguishable; assert the error points to the exact 3.1 license URL, `HF_TOKEN`, and re-run.
- `test_pyannote_provider_preserves_speaker_segments_schema_version`: call `diarize_to_file(..., provider="pyannote")` with a fake pyannote annotation and assert the output wrapper keeps `schema_version == "speaker_segments.v1"`.
- `test_pyannote_provider_normalizes_output_start_before_end`: fake pyannote turns with valid timings and assert every returned segment has numeric `start`, numeric `end`, and `start < end`.
- `test_pyannote_provider_rejects_invalid_turn_as_diarization_error`: fake a pyannote output with a zero-length or negative segment and assert normalization raises `DiarizationError`, not `DiarizationProviderError`.
- `test_pyannote_provider_does_not_leak_hf_token_to_error_or_artifact`: set `HF_TOKEN` to a sentinel value, force a provider failure or write a successful artifact through a fake pipeline, and assert the sentinel is absent from exception text and JSON.
- `test_pyannote_real_two_speaker_clip_detects_two_labels`: env-gated real test with `PAE_PYANNOTE_REAL=1` and `HF_TOKEN`; run a known short 2-speaker clip and assert exactly two distinct `speaker_id` values.
- `test_pyannote_real_one_speaker_clip_detects_one_label`: env-gated real test; run a short monologue fixture and assert exactly one distinct `speaker_id`.
- `test_pyannote_pipeline_is_constructed_once_per_provider_instance`: fake `Pipeline.from_pretrained()` call count, call `diarize()` twice on one provider instance, and assert the pipeline is loaded once.

## 5. Design Decisions

### Pipeline lifecycle

Decision: construct the pyannote pipeline once per `PyannoteDiarizationProvider` instance and reuse it for subsequent `diarize()` calls.

Rejected alternative: construct the pipeline once per `diarize()` call. That minimizes resident memory after each call only if the object is discarded immediately, but it makes every file pay the model cold-start and cache-check cost. The provider instance is the smallest local cache boundary and keeps tests deterministic with a fake loader call count.

### Overlapping segments

Decision: preserve pyannote overlaps in `speaker_segments.v1` for PR-C2 unless the implementer confirms downstream consumers require a non-overlap invariant. The current `normalize_speaker_segments()` validates each segment independently and does not reject overlapping time ranges.

Rejected alternative: collapse overlaps by speaker priority or longest-duration winner. That creates a hidden diarization policy before PR-D/PR-E define how overlapping speech should be consumed and could erase legitimate crosstalk. This is the main schema ambiguity: if downstream code assumes non-overlap, get a human decision before implementation.

### Speaker-count controls

Decision: do not expose new CLI flags in the first PR-C2 pass unless pyannote's defaults fail the required 1-speaker or 2-speaker fixtures. Allow internal provider options to pass `min_speakers` / `max_speakers` later through `**options`, but keep the user-facing CLI stable for this integration PR.

Rejected alternative: add `--min-speakers` and `--max-speakers` immediately. Those flags are useful for production tuning, but they expand the CLI contract before the real provider has baseline behavior and tests. Add them in a follow-up if real fixtures show default clustering is unstable.

### Device selection

Decision: default to CPU and optionally move the pipeline to CUDA only when `torch.cuda.is_available()` returns true and the implementation has imported torch lazily inside the provider path. Do not require CUDA wheels or GPU availability.

Rejected alternative: require an explicit `--device cuda` or install a CUDA-specific dependency set for PR-C2. That would make the first real integration harder to run on laptops and CI-like dev environments. CPU default matches the local-first project posture, while CUDA auto-use can reduce runtime when available.

### Error class boundary

Decision: use `DiarizationProviderError` for missing dependency, missing token, Hugging Face license/auth failures, model download/cache availability failures, and pyannote pipeline construction failures. Use `DiarizationError` for invalid normalized segment data after the provider returns an annotation.

Rejected alternative: wrap every pyannote path error in `DiarizationError`. That loses the distinction the current code already documents: provider availability/configuration failures are actionable setup problems, while `DiarizationError` means the diarization input/output data itself is invalid.

## 6. Out of Scope

- Speaker identity consistency across episodes or stable person naming.
- Real-time or streaming diarization.
- Fine-tuning pyannote models or training custom diarization heads.
- Custom embeddings or speaker enrollment.
- Overlapping-speech post-processing beyond preserving or documenting what `speaker_segments.v1` can represent.
- Alternative pyannote versions, including `speaker-diarization-community-1`, unless 3.1 becomes unavailable.
- NeMo, WhisperX diarization, Lattifai integration, or any ASR/alignment provider changes.
- CLI UX expansion beyond what is necessary to call the existing `pyannote` provider path.

## 7. Verification Plan

Core verification without real HF credentials:

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider tests/test_diarization.py
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider tests/test_diarization_pyannote_real.py -k "not pyannote_real"
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests
git ls-files .omx
```

Real-provider verification with accepted license and token:

```bash
export HF_TOKEN=<token provided out-of-band>
export PAE_PYANNOTE_REAL=1
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --extra diarize-pyannote --group dev pytest -q -p no:cacheprovider tests/test_diarization_pyannote_real.py
```

Manual smoke on a real short clip:

```bash
export HF_TOKEN=<token provided out-of-band>
uv run --extra diarize-pyannote python -m podcast_auto_editor diarize path/to/short-two-speaker.wav \
  --provider pyannote \
  --out runs/short-two-speaker/speaker_segments.v1.json
python -m json.tool runs/short-two-speaker/speaker_segments.v1.json >/tmp/speaker_segments.pretty.json
```

Before claiming done, inspect the JSON for `schema_version: "speaker_segments.v1"`, at least one segment, numeric `start`/`end`, `start < end`, expected distinct speaker labels for the fixture, and absence of the token string. Also run the repository's broader gate if this PR is close to merge:

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider
./scripts/smoke.sh
```

## 8. Implementation Handoff Brief

- Start with tests; keep core tests no-network and no-token by faking pyannote imports/pipeline output.
- Do not import `pyannote.audio`, `torch`, or Hugging Face modules at `podcast_auto_editor.diarization` module import time.
- Read `HF_TOKEN` only from the environment and pass it as `use_auth_token=os.environ.get("HF_TOKEN")`; never log, store, or serialize it.
- Convert pyannote annotations to the current `speaker_segments.v1` segment list, then call `normalize_speaker_segments()`.
- Preserve overlapping pyannote turns unless a human explicitly decides `speaker_segments.v1` must become non-overlapping.
- Keep dependency/auth/license failures as `DiarizationProviderError`; keep malformed output as `DiarizationError`.
- Add `docs/runbooks/pyannote-setup.md` in the implementation PR, including license acceptance and `hf download pyannote/speaker-diarization-3.1` pre-cache instructions.
- Gate real-model pytest with both `PAE_PYANNOTE_REAL=1` and `HF_TOKEN`; normal CI must remain slim and offline.
- Do not broaden the CLI unless the real fixtures prove default speaker clustering needs user-supplied min/max speaker counts.
