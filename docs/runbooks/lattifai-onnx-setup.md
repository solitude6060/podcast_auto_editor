# Runbook: Lattifai ONNX Setup (LattifAI/Lattice-1)

**Provider**: `lattifai`  
**Plan**: `docs/plans/2026-05-18-pr-x4-1-lattifai-onnx-air-gap.md`  
**License**: Apache-2.0  
**Inference**: fully offline — audio, model weights, and alignment artifacts stay on-machine.

---

## Prerequisites

- Python 3.11+
- `uv` package manager (or `pip`)
- `huggingface-cli` (`pip install huggingface_hub[cli]` or `uv tool install huggingface_hub[cli]`)
- ~600 MB free disk space for model weights

---

## Step 1 — Install the optional dependency group

```bash
uv sync --extra align-lattifai
```

This installs `onnxruntime>=1.0` (CPU provider).

`align-lattifai` is a PEP 621 optional-dependency extra defined under
`[project.optional-dependencies]` in `pyproject.toml`. Use `--extra` (not
`--group`) with `uv sync`, or `pip install .[align-lattifai]` for standard
pip installs.

**GPU users (CUDA):** install the GPU variant instead and skip the CPU package:

```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

**Apple Silicon (CoreML):** use `onnxruntime-silicon` from the ONNX Runtime release page instead.

---

## Step 2 — Download Lattice-1 model files

```bash
huggingface-cli download LattifAI/Lattice-1 \
    --local-dir ~/.cache/podcast-auto-editor/models/Lattice-1
```

To pin a specific revision (recommended for regulated deployments):

```bash
huggingface-cli download LattifAI/Lattice-1 \
    --revision <commit-sha> \
    --local-dir ~/.cache/podcast-auto-editor/models/Lattice-1
```

Record the commit SHA and file hashes in your deployment manifest.

---

## Step 3 — Verify model files

Run this before first use to confirm all required files are present:

```bash
ls -lh ~/.cache/podcast-auto-editor/models/Lattice-1/
```

Expected files (all must be present):

| File | Size (approx) | Purpose |
|---|---|---|
| `acoustic_opt.onnx` | ~129 MB | Acoustic emission model (required) |
| `config.json` | 82 B | Sample rate + frame config |
| `words.bin` | ~1 MB | Pronunciation dictionary / vocabulary |
| `transition.bin` | ~508 KB | Lattice transition model |
| `event.bin` | ~18 KB | Event sidecar |
| `event.data` | ~343 MB | Event dataset |
| `g2pp.bin` | ~16 KB | Grapheme-to-phoneme model (small) |
| `g2pp.safetensors` | ~117 MB | Grapheme-to-phoneme weights |

`acoustic_opt.onnx` is the only file checked at startup. The others are used
by the decoder (see decode blocker note below).

---

## Step 4 — Set the environment variable

```bash
export PAE_LATTIFAI_ONNX_PATH="$HOME/.cache/podcast-auto-editor/models/Lattice-1"
```

Add to your shell profile (`~/.zshrc`, `~/.bashrc`) for persistence.

Alternatively, pass `model_path=` directly to the provider:

```python
provider = LattifaiAlignmentProvider()
words = provider.align(audio_path, segments, model_path="/path/to/Lattice-1")
```

---

## Step 5 — Verify setup

```bash
PAE_LATTIFAI_ONNX_PATH="$HOME/.cache/podcast-auto-editor/models/Lattice-1" \
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor \
uv run --group dev --group align-lattifai \
    pytest -q -p no:cacheprovider tests/test_alignment_lattifai_real.py
```

Env-gated tests will run (instead of skip) when `PAE_LATTIFAI_ONNX_PATH` is set.

---

## Air-gap guarantee

This implementation intentionally bypasses `lattifai-python` (the official SDK).
The SDK constructs a `SyncAPIClient` that may phone home for quota / usage
tracking even though the model is local. This provider:

- Does NOT import `lattifai`, `lattifai_core`, or `SyncAPIClient`
- Does NOT make any network calls at inference time
- Loads `acoustic_opt.onnx` directly via `onnxruntime`
- Reads all sidecar files (words.bin, transition.bin, etc.) from the local directory

---

## Decode blocker (as of PR-X4.1, 2026-05-18)

The ONNX acoustic model produces emission log-probabilities
`(1, T_sub, vocab_size)`. Decoding these back to word timestamps requires a
lattice/FST decoder (`k2` library upstream). `k2` has no Python 3.11 PyPI
wheel, so it cannot be installed in this project (requires Python >=3.11).

**Current status**: the provider validates model path + onnxruntime availability,
returns `[]` for empty transcripts, and raises `AlignmentProviderError` with a
clear blocker message for non-empty transcripts.

**Required next step**: a follow-up PR must implement one of:
- Pure-Python CTC greedy decode against `words.bin` (if ONNX output is CTC-compatible)
- A subprocess shim running k2 in a Python 3.9/3.10 venv
- A contributed local-only decode path that eliminates the k2 dependency

Until then, use `--provider mock` or `--provider whisperx` for production alignment.
