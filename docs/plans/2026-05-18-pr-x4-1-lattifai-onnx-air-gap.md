# PR-X4.1 Lattifai ONNX Air-Gap Plan

Date: 2026-05-18

## 1. Why

This PR unblocks a strict local-first Lattifai alignment path for Chinese podcast word timestamps. The 2026-05-17 research decision accepted the user's Plan B: bypass the official `lattifai-python` SDK and load `LattifAI/Lattice-1` directly with ONNX Runtime, rather than Plan A where the SDK remains on the runtime path and may initialize `SyncAPIClient` for quota / usage tracking.

The local-first invariant is: audio, transcript text, model inference, and alignment artifacts must stay on the operator's machine at inference time. `docs/research/2026-05-17-chinese-asr-models.md` section 2.2 confirms the Lattice-1 model itself is Apache-2.0, ONNX, and local, but the SDK path is not acceptable for full air-gap operation. The Hugging Face model card confirms Lattice-1 is a forced-alignment model, supports English / Chinese / German, uses ONNX runtime support, and is Apache-2.0: <https://huggingface.co/LattifAI/Lattice-1>.

Context read notes:
- `/home/ma/.claude/CLAUDE.md` was available and reinforces plan-first, TDD, surgical changes, and docs-only exceptions.
- Repo-root `CLAUDE.md` was requested but not present in this worktree; implementer should continue using `AGENTS.md` plus the global rules.
- `podcast_auto_editor/alignment.py` currently has a deferred-error `LattifaiAlignmentProvider` stub and a `WhisperXAlignmentProvider` pattern that lazy-imports optional dependencies and raises `AlignmentProviderError`.
- `tests/test_alignment.py` already pins provider error class behavior, `align_to_file` no-write-on-provider-error behavior, schema version emission, and CJK per-character mock tokenization.

## 2. Constraints

- No telemetry and no network at inference time. The implementation must not import or instantiate `lattifai`, `lattifai_core`, `SyncAPIClient`, or any SDK path that can phone home.
- No auto-download. Model files must be pre-downloaded manually by the operator using the runbook before inference starts.
- `onnxruntime` must be a lazy import inside the Lattifai provider path so core install, import, and tests remain zero-heavy-dependency.
- Add an optional dependency group named `align-lattifai` in `pyproject.toml`.
- Preserve the `AlignmentProviderError` / `AlignmentError` hierarchy: provider setup, missing model, and dependency failures raise `AlignmentProviderError`; malformed provider output still raises `AlignmentError` through `normalize_word_alignments`.

## 3. Deliverables

1. Modify `podcast_auto_editor/alignment.py`.
   - Replace `LattifaiAlignmentProvider.align()` deferred-error stub with a real ONNX-driven implementation.
   - Lazy-import `onnxruntime` only after validating that a model path was provided.
   - Accept `model_path` from `align(..., model_path=...)` and fall back to `PAE_LATTIFAI_ONNX_PATH`.
   - Treat `model_path` as the path to the pre-downloaded Lattice-1 model directory, not just a single file, because the Hugging Face repo includes `acoustic_opt.onnx`, `config.json`, `words.bin`, `transition.bin`, `event.*`, and G2P files.
   - Raise a clear `AlignmentProviderError` when the model directory or required `acoustic_opt.onnx` file is missing. The message must say how to set `model_path` or `PAE_LATTIFAI_ONNX_PATH`; do not keep the old "deferred to PR-X4.1" message.
   - Return normalized `word_alignments.v1` word entries by calling `normalize_word_alignments()` before returning.
   - IMPLEMENTER MUST VERIFY — source unknown: the exact ONNX input names, output tensor names, required preprocessing sample rate, and decoder mapping are not specified in the local research file or public model card.

2. Modify `pyproject.toml`.
   - Add dependency group:
     ```toml
     align-lattifai = [
         "onnxruntime>=1.18",
     ]
     ```
   - Add a nearby TOML comment documenting that CPU is the default, while CUDA / CoreML users should install the matching ONNX Runtime provider package outside the core dependency group after validating their platform.
   - Do not add `lattifai` or SDK-adjacent dependencies.

3. Add `docs/runbooks/lattifai-onnx-setup.md`.
   - Manual setup steps:
     ```bash
     hf download LattifAI/Lattice-1 --local-dir ~/.cache/podcast-auto-editor/models/Lattice-1
     export PAE_LATTIFAI_ONNX_PATH="$HOME/.cache/podcast-auto-editor/models/Lattice-1"
     ```
   - Include a verification step that lists `acoustic_opt.onnx`, `config.json`, and tokenizer / lexicon sidecar files before running the provider.
   - State explicitly that runtime inference is offline and that the implementation intentionally bypasses `lattifai-python`.

4. Add `tests/test_alignment_lattifai_real.py`.
   - New env-gated integration tests skipped unless `PAE_LATTIFAI_ONNX_PATH` is set.
   - Cover empty transcript -> empty alignments.
   - Cover a single-segment Chinese transcript -> per-character word entries with monotonic timestamps.
   - Cover missing-model error message clarity without requiring the real model.

5. Modify `tests/test_alignment.py`.
   - Update `test_lattifai_provider_raises_clear_error_when_called` if message semantics change from deferred integration to model-path-required.
   - Keep the class assertions: raised exception is `AlignmentProviderError` and not raw `ImportError`.

## 4. TDD Test List

- `test_lattifai_missing_model_path_raises_alignment_provider_error`: with no `model_path` and no `PAE_LATTIFAI_ONNX_PATH`, provider raises `AlignmentProviderError` explaining both configuration options.
- `test_lattifai_missing_model_file_raises_alignment_provider_error`: with a temp directory missing `acoustic_opt.onnx`, provider raises `AlignmentProviderError` naming the expected file.
- `test_lattifai_lazy_import_failure_raises_alignment_provider_error`: monkeypatch import so `onnxruntime` is unavailable after a valid-looking model path is configured; provider raises `AlignmentProviderError` with install guidance for `align-lattifai`.
- `test_lattifai_env_var_model_path_happy_path`: env-gated real-model test; with `PAE_LATTIFAI_ONNX_PATH` set, provider aligns a short fixture and returns normalized words.
- `test_lattifai_tokenizer_local_files_only_flag`: any tokenizer / lexicon loader that uses Hugging Face helpers must pass `local_files_only=True`; if the final implementation uses only local sidecar files and no Hugging Face helper, this test should assert the helper path is never called.
- `test_lattifai_schema_version_preserved_in_output`: `align_to_file(..., provider="lattifai")` writes `schema_version == SCHEMA_VERSION` when the env-gated provider succeeds.
- `test_lattifai_empty_transcript_returns_empty_alignments`: env-gated real-model test; empty transcript returns `[]` without invoking decoder work that requires transcript tokens.
- `test_lattifai_single_segment_chinese_returns_word_entries`: env-gated real-model test; `"你好世界"` yields one entry per Chinese character, preserving text order and non-overlapping timestamps.

Red phase order:
1. Add non-env unit tests for missing path, missing file, lazy import failure, and changed current-provider error semantics.
2. Add env-gated real-model tests and confirm they skip cleanly without `PAE_LATTIFAI_ONNX_PATH`.
3. Implement the provider.
4. Run the env-gated tests only on a machine with the manually downloaded model.

## 5. Design Decisions

### Tokenizer Source

Decision: prefer a local sidecar-file loader / shim based on the files in the pre-downloaded `LattifAI/Lattice-1` directory, and use Hugging Face helper APIs only if the sidecar format cannot be parsed directly.

Rejected alternative: `transformers.AutoTokenizer.from_pretrained(model_dir, local_files_only=True)` as the primary path.

Why: the model repo file list does not show a standard Hugging Face tokenizer layout; it includes `words.bin`, `g2pp.bin`, `g2pp.safetensors`, and transition/event sidecars. Adding `transformers` would make the optional dependency group heavier without proof that `AutoTokenizer` can load this model. If the implementer discovers upstream code uses a standard tokenizer, they may switch, but must keep `local_files_only=True` and document the dependency change in the same PR.

### Decoder Algorithm

Decision: implement the decoder to match Lattice-1's upstream forced-alignment algorithm after inspecting `lattifai-python` source and the downloaded model files.

Rejected alternative: assume generic CTC greedy decoding from the ONNX logits.

Why: the model card says Lattice-1 is a forced-alignment model with word-level timestamps, but it does not document whether output should be decoded as CTC greedy, beam search, finite-state / transition-lattice alignment, or another forced-alignment graph. The model repo includes sidecars such as `transition.bin`, `event.bin`, `event.data`, and `words.bin`, which suggests a decoder more specific than plain logits. IMPLEMENTER MUST VERIFY — source unknown: exact output tensor format and decoder algorithm are not confirmed by local files or the public model card.

### Error Hierarchy

Decision: use `AlignmentProviderError` for provider setup failures: missing `model_path`, missing `PAE_LATTIFAI_ONNX_PATH`, missing model files, missing `onnxruntime`, unsupported provider device, or upstream ONNX session creation failure. Use `AlignmentError` for invalid normalized alignment output and let `normalize_word_alignments()` enforce schema details.

Rejected alternative: collapse all Lattifai failures into `AlignmentError`.

Why: existing provider tests and the `WhisperXAlignmentProvider` pattern distinguish "provider cannot run" from "alignment data is invalid." Keeping that contract lets `align_to_file()` surface setup failures without writing partial artifacts.

### Optional Dependency Group Name

Decision: name the group `align-lattifai`.

Rejected alternative: `lattifai`.

Why: `lattifai` is ambiguous with the official SDK, which this PR must bypass. `align-lattifai` says this group belongs to the alignment provider and does not imply SDK installation.

Rejected alternative: `air-gap-align`.

Why: it describes a deployment property rather than the provider. Future air-gapped providers should get their own precise optional groups instead of sharing a vague one.

### ONNX File Integrity On Load

Decision: trust-on-load for PR-X4.1, with runbook-visible manual download and file presence checks.

Rejected alternative: require sha256 verification in the provider before every load.

Why: the plan does not yet have pinned hashes for `LattifAI/Lattice-1`, and the model repo may update large files. Adding a hardcoded hash now would either block legitimate manual updates or create a false sense of auditability. The runbook should tell operators to pin a Hugging Face revision and record hashes for regulated deployments; automatic verification can be a follow-up once the exact revision is selected.

## 6. Out of Scope

- GPU acceleration tuning.
- Batched alignment.
- Beam-search parameter tuning.
- Mandarin vs Cantonese tokenizer differences.
- Automatic fallback to WhisperX if Lattifai fails; caller/provider selection remains the caller's responsibility.

## 7. Verification Plan

Happy path without model, must pass on any development machine:

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider tests/test_alignment.py tests/test_alignment_lattifai_real.py
```

Env-gated real-model tests, run only after manual model download:

```bash
export PAE_LATTIFAI_ONNX_PATH="$HOME/.cache/podcast-auto-editor/models/Lattice-1"
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev --group align-lattifai pytest -q -p no:cacheprovider tests/test_alignment_lattifai_real.py
```

Compile check:

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor/
```

Manual model-loading smoke test:

```bash
PAE_LATTIFAI_ONNX_PATH="$HOME/.cache/podcast-auto-editor/models/Lattice-1" \
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor \
uv run --group dev --group align-lattifai python - <<'PY'
from podcast_auto_editor.alignment import LattifaiAlignmentProvider

provider = LattifaiAlignmentProvider()
words = provider.align(
    "fixtures/audio/short_zh.wav",
    [{"start": 0.0, "end": 2.0, "text": "你好世界"}],
)
print(words[:4])
PY
```

Full PR boundary verification before claiming done:

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests
git ls-files .omx
git log -1 --pretty=%B | rg "Co-authored-by" && exit 1 || true
```

## 8. Implementation Handoff Brief

Build PR-X4.1 as a strict air-gapped Lattifai ONNX provider. Touch only `podcast_auto_editor/alignment.py`, `pyproject.toml`, `docs/runbooks/lattifai-onnx-setup.md`, `tests/test_alignment.py`, and new `tests/test_alignment_lattifai_real.py`.

Land red tests first: missing model path, missing model file, lazy `onnxruntime` import failure, local-only tokenizer guard, schema preservation, and env-gated real-model cases. Confirm env-gated tests skip without `PAE_LATTIFAI_ONNX_PATH`.

Implement the smallest provider path that loads `acoustic_opt.onnx` from a pre-downloaded `LattifAI/Lattice-1` directory and returns normalized `word_alignments.v1` entries. Do not import or instantiate the official `lattifai-python` SDK.

IMPLEMENTER MUST VERIFY — source unknown: inspect upstream `lattifai-python` and/or downloaded model files for audio preprocessing, input tensor names, output tensor names, token / word mapping, transition handling, and decoder algorithm before writing the green implementation.

Do not auto-download the model, do not add runtime network calls, do not change README files, do not add WhisperX fallback, and do not broaden dependency groups beyond the Lattifai alignment path.
