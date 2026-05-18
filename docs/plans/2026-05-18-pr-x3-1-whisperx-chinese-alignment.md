# PR-X3.1 Plan: WhisperX Chinese Phoneme Alignment

## 1. Why

WhisperX is now the primary air-gap alignment path for Chinese podcasts. PR-X4.1's Lattifai ONNX-direct route hit a hard blocker: the decoder requires `k2` with no Python 3.11 wheel, and the available SDK tokenizer path posts to a hosted backend, which conflicts with the project's air-gap requirement.

The user chose to land the X4.1 scaffolding separately and make WhisperX Chinese phoneme alignment the actually shipping path. This plan replaces the current deferred-error `WhisperXAlignmentProvider` stub in `podcast_auto_editor/alignment.py` with a real local alignment provider while preserving the existing `word_alignments.v1` schema.

`docs/plans/2026-05-18-pr-x4-1-lattifai-onnx-air-gap.md` was requested as a structure reference but is absent in this worktree. This plan mirrors the requested nine-section structure and uses the available Lattifai context from `alignment.py` plus `docs/research/2026-05-17-chinese-asr-models.md`.

## 2. Constraints

- Add WhisperX as a new PEP 621 optional extra under `[project.optional-dependencies]`, named `align-whisperx`. Do not use `[dependency-groups]` for this optional runtime dependency.
- The `align-whisperx` extra contains `whisperx` and `torch`; base installs remain dependency-light.
- Use `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn` as the documented Chinese phoneme model recommendation.
- Model weights are manually downloaded or pre-cached with `hf download`; runtime must not auto-download model weights.
- Keep `import whisperx` inside `WhisperXAlignmentProvider.align()` only. Do not import WhisperX at module top level.
- Provider requires an explicit model path from `model_path=` or `PAE_WHISPERX_ALIGN_MODEL`. No silent remote-model fallback.
- Raise `AlignmentProviderError` for dependency, setup, model-path, config, and provider runtime failures.
- Raise `AlignmentError` for malformed transcript/audio/alignment data and schema validation failures.
- Preserve `word_alignments.v1`: flat `words` entries are normalized through `normalize_word_alignments()`.

## 3. Deliverables

a. `podcast_auto_editor/alignment.py`

Replace `WhisperXAlignmentProvider.align()` with the real provider body:

- If `transcript_segments` is empty, return `[]` before loading WhisperX. This lets `align_to_file()` write a valid empty `word_alignments.v1` artefact and gives the schema-preservation test a real file-write path.
- Resolve the Chinese align model path from `options.get("model_path")` first, then `os.environ.get("PAE_WHISPERX_ALIGN_MODEL")`.
- If the resolved model path is missing for a non-empty transcript, raise `AlignmentProviderError` naming both `model_path` and `PAE_WHISPERX_ALIGN_MODEL`.
- Lazy-import `whisperx` inside `align()`. Lazy-import `torch` inside `align()` only if the implementation uses CUDA auto-detection.
- Select `device` from `options.get("device")`; otherwise use `cuda` when `torch.cuda.is_available()` is true and `cpu` otherwise. If `torch` cannot import but WhisperX imports, fall back to `cpu` or raise `AlignmentProviderError` only if WhisperX itself cannot run.
- Load audio with `audio = whisperx.load_audio(str(audio_path))`.
- Load the alignment model with `whisperx.load_align_model(language_code="zh", model_name=model_path, device=device)`. Context7/WhisperX docs show the current signature as `load_align_model(language_code, device, model_name=None, model_dir=None)`.
- Align with `whisperx.align(transcript_segments, model, metadata, audio, device)`. Context7/WhisperX docs show the current signature as `align(segments, model, metadata, audio, device, interpolate_method="nearest", return_char_alignments=False, print_progress=True)`.
- Flatten WhisperX output from `result["segments"][*]["words"][*]` when present; otherwise use `result["word_segments"]`.
- Map each WhisperX word item to `{ "start": item["start"], "end": item["end"], "text": item.get("word", item.get("text")) }`.
- Drop WhisperX `score` for PR-X3.1; do not invent a confidence field in `word_alignments.v1`.
- Pass the flattened list through `normalize_word_alignments()` before returning.
- Wrap provider setup/execution exceptions in `AlignmentProviderError`, but let `AlignmentError` from normalization remain visible as data/schema failure.

b. `pyproject.toml`

Add:

```toml
[project.optional-dependencies]
align-whisperx = [
  "whisperx",
  "torch",
]
```

If `[project.optional-dependencies]` already exists by implementation time, merge into it. Keep `[dependency-groups] dev = ["pytest>=6.2"]` unchanged.

c. `docs/runbooks/whisperx-alignment-setup.md`

Create a manual setup runbook:

- Install: `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv sync --extra align-whisperx --group dev` or the project's equivalent install command.
- Download before air-gap use: `hf download jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn --local-dir /path/to/models/wav2vec2-large-xlsr-53-chinese-zh-cn`.
- Configure: `export PAE_WHISPERX_ALIGN_MODEL=/path/to/models/wav2vec2-large-xlsr-53-chinese-zh-cn`.
- Smoke test:

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor \
PAE_WHISPERX_ALIGN_MODEL=/path/to/models/wav2vec2-large-xlsr-53-chinese-zh-cn \
uv run python -m podcast_auto_editor align /path/to/short-zh.wav \
  --provider whisperx \
  --transcript-json /path/to/short-zh-transcript.v1.json \
  --out /tmp/word_alignments.v1.json
```

- Document alternative phoneme models for Mandarin, Cantonese, and Taiwanese Mandarin as user-supplied choices. PR-X3.1 wires only the `language_code="zh"` path and does not validate dialect quality.
- State explicitly that runtime must not fetch model weights automatically.

d. `tests/test_alignment_whisperx_real.py` (new)

Add env-gated real-provider coverage:

- Empty transcript through `align_to_file(..., provider="whisperx")` writes a valid artefact with `schema_version == "word_alignments.v1"` and `words == []`.
- Short Chinese transcript returns ordered per-character or word entries.
- Missing model path raises `AlignmentProviderError`.
- Lazy import failure raises `AlignmentProviderError` instead of leaking `ImportError`.
- Schema preservation checks the exact file shape written by `align_to_file()`.

e. `tests/test_alignment.py`

Tighten `test_whisperx_provider_raises_clear_error_when_called` to match the new config-required message for non-empty transcripts. Keep the existing class-boundary assertion: failure must be `AlignmentProviderError`, not raw `ImportError`.

## 4. TDD Test List

- `test_whisperx_empty_transcript_writes_empty_artefact`: call `align_to_file("audio.wav", [], out, provider="whisperx")`; assert the file is written with `schema_version == SCHEMA_VERSION`, `audio_path`, and `words == []`. This intentionally exercises file-write code instead of short-circuiting on a provider blocker.
- `test_whisperx_missing_model_path_raises_provider_error`: with no `model_path` kwarg and no `PAE_WHISPERX_ALIGN_MODEL`, call the provider with a non-empty transcript and assert an actionable `AlignmentProviderError`.
- `test_whisperx_lazy_import_failure_raises_provider_error`: configure a fake local `model_path`, simulate missing `whisperx`, and assert the provider wraps the import failure in `AlignmentProviderError`.
- `test_whisperx_env_gated_happy_path`: skip unless `PAE_WHISPERX_ALIGN_MODEL` and a tiny local Chinese audio fixture are available; align a short transcript and assert non-empty ordered timings.
- `test_whisperx_chinese_per_character_alignment_correctness`: with the env-gated fixture, align `你好世界`; assert output text order matches the transcript at character or word granularity accepted by WhisperX's Chinese model.
- `test_whisperx_schema_preservation_empty_transcript`: duplicate the schema assertion against the empty-transcript path if the real happy-path fixture is unavailable, so schema preservation is always checked without network or model download.
- `test_whisperx_error_class_boundary_provider_vs_data`: provider setup/config/import failures raise `AlignmentProviderError`; malformed WhisperX word output missing `start`, `end`, or word text reaches `normalize_word_alignments()` and raises `AlignmentError`.

## 5. Design Decisions

a. Phoneme model name default

Decision: document `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn` as the recommended model, but force the runtime to receive `model_path` or `PAE_WHISPERX_ALIGN_MODEL`.

Rejected alternative: hardcode the Hugging Face model ID as a silent provider default. Rejected because WhisperX/Transformers may auto-download remote weights when given a model ID, which violates the air-gap path.

b. WhisperX batch_size / chunk_size knobs

Decision: keep PR-X3.1 on hardcoded WhisperX alignment defaults, with only internal `**options` passthrough if the current WhisperX API accepts a specific option and tests cover it. Do not add public CLI knobs.

Rejected alternative: expose `batch_size` and `chunk_size` CLI flags now. Rejected because this PR is about correctness, offline setup, and schema mapping; GPU tuning belongs after real-episode latency is measured.

c. Device selection

Decision: use explicit `device` when provided; otherwise choose `cuda` only when `torch.cuda.is_available()` is true, else `cpu`.

Rejected alternative: force CPU for deterministic local behavior. Rejected because 60-90 minute podcast alignment can be slow and the project already supports local GPU profiles.

d. Output format mapping

Decision: flatten WhisperX `{segments: [{words: [{start, end, word, score}]}]}` or `word_segments` into `word_alignments.v1` flat entries `{start, end, text}`. Drop `score` in PR-X3.1.

Rejected alternative: preserve WhisperX `score` as `confidence`. Rejected because `word_alignments.v1` does not define confidence semantics; adding it now would create a schema contract without downstream consumers or validation rules.

e. WhisperX whisper_model size for alignment metadata

Decision: do not load a Whisper ASR model in the alignment provider. `WhisperXAlignmentProvider` receives transcript segments from the existing transcription path and only loads the Chinese wav2vec2 alignment model.

Rejected alternative: match `asr.py`'s large-v3 or another Whisper model inside the alignment provider. Rejected because that would mix transcription and forced alignment responsibilities and introduce unnecessary heavy model loading.

f. Error class boundary

Decision: `AlignmentProviderError` covers missing optional dependencies, missing model path, lazy-import failures, model load failures, and WhisperX runtime/provider failures. `AlignmentError` covers invalid transcript/audio/alignment data and normalization failures.

Rejected alternative: collapse all alignment failures into `AlignmentError`. Rejected because current tests and CLI diagnostics distinguish "provider cannot run" from "data is invalid."

## 6. Out of Scope

- GPU tuning beyond basic device selection.
- Batched alignment optimization.
- Multi-language alignment beyond `language_code="zh"`.
- Pronunciation variants and dialect-specific selection.
- Fallback to Lattifai if WhisperX fails.
- Custom phoneme model training.
- Diarization or speaker assignment.
- Schema changes for WhisperX confidence scores.

## 7. Verification Plan

Implementer runs the local no-network checks first:

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider tests/test_alignment.py
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider tests/test_alignment_whisperx_real.py
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests
git ls-files .omx
git log -1 --format=%B
```

Then run the real-model path after manual model download:

```bash
hf download jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn \
  --local-dir /path/to/models/wav2vec2-large-xlsr-53-chinese-zh-cn

UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor \
PAE_WHISPERX_ALIGN_MODEL=/path/to/models/wav2vec2-large-xlsr-53-chinese-zh-cn \
uv run --group dev pytest -q -p no:cacheprovider tests/test_alignment_whisperx_real.py

UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor \
PAE_WHISPERX_ALIGN_MODEL=/path/to/models/wav2vec2-large-xlsr-53-chinese-zh-cn \
uv run python -m podcast_auto_editor align /path/to/short-zh.wav \
  --provider whisperx \
  --transcript-json /path/to/short-zh-transcript.v1.json \
  --out /tmp/word_alignments.v1.json
```

Expected evidence:

- Non-WhisperX alignment tests pass without installing `whisperx`.
- Env-gated tests skip cleanly when `PAE_WHISPERX_ALIGN_MODEL` is unset.
- Real WhisperX tests pass when the local model path is configured.
- Compileall succeeds.
- `git ls-files .omx` prints nothing.
- Recent commit message contains no `Co-authored-by`.

## 8. Implementation Handoff Brief

Implement PR-X3.1 as a surgical provider replacement.

Only change `WhisperXAlignmentProvider`, the optional dependency metadata, the WhisperX setup runbook, and tests named in this plan.

Keep heavy imports lazy and require `model_path` or `PAE_WHISPERX_ALIGN_MODEL` for non-empty transcripts.

Use `whisperx.load_audio()`, `whisperx.load_align_model(language_code="zh", model_name=model_path, device=device)`, then `whisperx.align(transcript_segments, model, metadata, audio, device)`.

Flatten WhisperX words into `{start, end, text}` and normalize through `normalize_word_alignments()`.

Use `AlignmentProviderError` for setup/provider failures and `AlignmentError` for bad data.

Lock behavior with failing tests first, including the empty-transcript schema-preservation file-write path.

Do not add fallback providers, new CLI tuning flags, auto-downloads, diarization, or schema score fields.

## 9. Open Questions / Risks

- WhisperX API stability across versions: Context7 currently documents `load_align_model(language_code, device, model_name=None, model_dir=None)` and `align(segments, model, metadata, audio, device, ...)`; the implementer must verify the installed version before coding.
- Phoneme model Hugging Face availability and license: `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn` is the recommended Chinese model, but availability/license should be rechecked before shipping setup docs.
- Latency for 60-90 minute podcast episodes: correctness and schema preservation come first; performance tuning may need a later PR after real episode measurements.
- CUDA wheel availability on the user's platform: PyTorch CUDA installation varies by OS/CUDA version; the runbook must document CPU fallback.
- Verification of WhisperX no-network-at-align-time claim: PR-X3.1 should test with pre-downloaded weights and an offline environment or network-disabled smoke run before calling the path air-gapped.
