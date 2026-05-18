# Runbook: pyannote Speaker Diarization Setup

This runbook covers the one-time operator steps to enable real speaker
diarization via `pyannote/speaker-diarization-3.1`.

## Prerequisites

- Python 3.11+ with `podcast-auto-editor` installed
- A Hugging Face account (free)
- `uv` (recommended) or `pip`

---

## Step 1 — Accept the model license

The `pyannote/speaker-diarization-3.1` model is gated. You must manually
accept the license before any code can download it.

1. Sign in to [huggingface.co](https://huggingface.co) (create a free account
   if you do not have one).
2. Open the model page:
   <https://huggingface.co/pyannote/speaker-diarization-3.1>
3. Click **"Agree and access repository"** (or the equivalent consent button
   shown on the page). You only need to do this once per HF account.

> Note: you must also accept the license for the segmentation sub-model used
> internally by pyannote 3.1:
> <https://huggingface.co/pyannote/segmentation-3.0>
> Open that page and accept the license there too.

---

## Step 2 — Generate a Hugging Face token

1. Go to <https://huggingface.co/settings/tokens>.
2. Click **"New token"**, give it a descriptive name (e.g. `podcast-editor`),
   choose **read** scope, and click **"Generate a token"**.
3. Copy the token value — it will not be shown again.

**Security**: treat this token like a password. Do not commit it to version
control, do not include it in config files, and do not paste it into chat.

---

## Step 3 — Export the token to your environment

```bash
export HF_TOKEN=hf_...your_token_here...
```

Add this to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.) so it
persists across sessions, or use a secrets manager appropriate for your
deployment environment.

The code reads `HF_TOKEN` from the environment only. It never prompts for
the token, never writes it to disk, and never includes it in any output.

---

## Step 4 — Install the optional dependency group

```bash
# Recommended: uv
uv sync --extra diarize-pyannote

# Alternative: pip
pip install 'podcast-auto-editor[diarize-pyannote]'
```

This installs `pyannote.audio>=3.1` and `torch>=2.0`. By default, CPU
wheels are fetched. If you want CUDA acceleration, install a CUDA-enabled
torch wheel first per <https://pytorch.org/get-started/locally/>, then
install the extra above.

---

## Step 5 — Pre-cache the model (optional but recommended)

The first `diarize` call downloads model weights from Hugging Face (~1 GB
depending on the model version). To do this once up front — useful for
offline or air-gapped use after caching:

```bash
huggingface-cli download pyannote/speaker-diarization-3.1 \
  --token "$HF_TOKEN"

# Also cache the segmentation sub-model:
huggingface-cli download pyannote/segmentation-3.0 \
  --token "$HF_TOKEN"
```

> Warning: first download may be large and network-bound. Run this on a
> connection where 1–2 GB is acceptable. Subsequent runs use the local cache
> at `~/.cache/huggingface/hub/` and do not re-download.

---

## Step 6 — Smoke test

Run a quick diarization on a short two-speaker clip:

```bash
export HF_TOKEN=hf_...your_token_here...

uv run --extra diarize-pyannote python -m podcast_auto_editor diarize \
  path/to/short-two-speaker.wav \
  --provider pyannote \
  --out runs/smoke/speaker_segments.v1.json

# Inspect the result
python -m json.tool runs/smoke/speaker_segments.v1.json
```

Expected output includes:
- `"schema_version": "speaker_segments.v1"`
- At least one segment with numeric `start`, `end`, and a `speaker_id` string
- `start < end` for every segment
- No occurrence of your token value anywhere in the JSON

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `DiarizationProviderError: pyannote.audio is not installed` | Extra not installed | Run `uv sync --extra diarize-pyannote` |
| `DiarizationProviderError: Access to ... is restricted` | License not accepted or wrong token | Accept license at the model page; verify `HF_TOKEN` is correct |
| `DiarizationProviderError: Failed to load ... HF_TOKEN` | Token missing or expired | `echo $HF_TOKEN` to check; generate a new token if blank |
| First run is slow (minutes) | Model downloading | Normal — model is ~1 GB; subsequent runs use local cache |
| `CUDA out of memory` | GPU memory too small | The pipeline auto-uses CPU when CUDA OOM occurs; or set `CUDA_VISIBLE_DEVICES=""` to force CPU |

---

## References

- Model card: <https://huggingface.co/pyannote/speaker-diarization-3.1>
- pyannote.audio docs: <https://github.com/pyannote/pyannote-audio>
- Hugging Face token settings: <https://huggingface.co/settings/tokens>
- PyTorch install selector: <https://pytorch.org/get-started/locally/>
