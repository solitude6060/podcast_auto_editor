# WhisperX Alignment Setup

## Install

```bash
uv sync --extra align-whisperx
```

## Model Download

```bash
huggingface-cli download jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn
```

## Environment

```bash
export PAE_WHISPERX_ALIGN_MODEL=/path/to/model
```

## Smoke Test

```bash
uv run python -c "from podcast_auto_editor.alignment import WhisperXAlignmentProvider; p = WhisperXAlignmentProvider(); print(p.align('audio.wav', []))"
```

## License

Apache 2.0 confirmed for `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn`: <https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn>

## CPU Latency

Not measured in sandbox env. Typical wav2vec2-large models process ~10x realtime on CPU. For a 60-min podcast expect ~6 min on CPU, ~30 sec on GPU. Measure with:

```bash
time uv run python -c "..."
```

on a 30-sec sample.

## Network Isolation

Not verified in sandbox env. Verification procedure: rename `~/.cache/huggingface` aside, set `PAE_WHISPERX_ALIGN_MODEL`, run smoke. If it completes without downloading, model is fully offline.

## Alternative Models

- Mandarin: `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn` (default).
- Cantonese: `CAiRE/wav2vec2-large-xlsr-cantonese`.
- Taiwanese: requires manual search on HF hub.
