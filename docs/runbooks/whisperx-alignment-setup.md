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

Use a local Chinese WAV fixture. If `fixtures/audio/short_30s_zh.wav` is not present in your checkout, create a 30-second Chinese sample or replace the path with your own local audio.

```bash
PAE_WHISPERX_ALIGN_MODEL=$HOME/.cache/podcast-auto-editor/models/wav2vec2-chinese \
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor \
uv run --extra align-whisperx python -c "
import time
from podcast_auto_editor.alignment import align_to_file
segs = [{'start': 0.0, 'end': 30.0, 'text': '你好，這是一個測試。'}]
t0 = time.time()
align_to_file('fixtures/audio/short_30s_zh.wav', segs, '/tmp/x3-1-bench.json', provider='whisperx')
print(f'duration: {time.time()-t0:.2f}s')
"
```

## Network Isolation

This check disables the default Hugging Face cache and exercises a non-empty alignment. Restore the cache after the command.

```bash
mv ~/.cache/huggingface ~/.cache/huggingface.bak
PAE_WHISPERX_ALIGN_MODEL=$HOME/.cache/podcast-auto-editor/models/wav2vec2-chinese \
uv run --extra align-whisperx python -c "
from podcast_auto_editor.alignment import align_to_file
segs = [{'start': 0.0, 'end': 30.0, 'text': '你好。'}]
align_to_file('fixtures/audio/short_30s_zh.wav', segs, '/tmp/x3-1-airgap.json', provider='whisperx')
print('PASS: alignment succeeded with HF cache disabled')
"
# Restore: mv ~/.cache/huggingface.bak ~/.cache/huggingface
```

## Alternative Models

- Mandarin: `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn` (default).
- Cantonese: `CAiRE/wav2vec2-large-xlsr-cantonese`.
- Taiwanese: requires manual search on HF hub.
