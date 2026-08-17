# Podcaster-ready AI MVP closeout

Date: 2026-05-18
Branch: `dev`

## Scope

This pass focused on the immediate podcaster blocker: producing publish-ready audio exports from a real episode and making quality failures understandable without reading raw JSON. AI work was limited to safe wiring and diagnostics because the local ASR packages and local OpenAI-compatible endpoint were not available in the current environment.

## Changes

- Audio render now uses measured two-pass FFmpeg loudnorm with channel layout conversion before loudness measurement.
- Lossy podcast exports reserve true-peak headroom and retry with larger headroom only for true-peak/clipping failures; the final encoded file still has to pass the configured quality gate.
- Pipeline metadata persists per-export quality reports and the failed profile before raising a quality error.
- CLI markdown/JSON reports and static HTML reports show per-profile check targets and actual values.
- `ai draft` and `explain --with-ai` can read `MINIMAX_API_KEY` from the environment for explicitly selected MiniMax-compatible endpoints without persisting the key.
- `ai doctor` reports optional Python packages for faster-whisper, qwen ASR, and pyannote as warnings.

## Real Audio Evidence

Input used locally: `/media/ma/1AF83466F83441F5/startup/podcast/ep1-test-soundtrack-20260429/Untitled_1 #08.wav`

Command:

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor bash scripts/walkthrough-real-podcast.sh --audio '/media/ma/1AF83466F83441F5/startup/podcast/ep1-test-soundtrack-20260429/Untitled_1 #08.wav' --out /tmp/pae-mvp-real-20260518-postfix4 --episode-id ep1-real-mvp
```

Result:

- Proposed/accepted deterministic silence cuts: 10
- Removed audio: 32.500s
- `archive-wav`: passed, actual loudness `-19.03` LUFS, true peak `-1.0` dB
- `podcast-stereo`: passed, actual loudness `-16.52` LUFS, true peak `-1.46` dB
- `podcast-mono`: passed, actual loudness `-19.85` LUFS, true peak `-2.05` dB
- Exported MP3s were written under `/tmp/pae-mvp-real-20260518-postfix4/runs/ep1-real-mvp/exports`.

## Deferred Items

- Real Chinese ASR was not run in this environment because `faster_whisper`, qwen ASR, and pyannote packages were not installed.
- Live AI draft from `qwen3.6-27b-turbo3` was not run because the local `/v1/models` endpoint was not reachable during this pass.
- Speech cleanup / retake cleanup remains gated behind reliable ASR plus review acceptance.
