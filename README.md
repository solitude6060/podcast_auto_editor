# Podcast Auto Editor

Local-first, CLI-first MVP for full-length podcast post-production.

The project uses a canonical reversible `timeline.v1` before media mutation. It is audio-first (WAV/MP3/M4A), optionally supports MP4 sync/export, and keeps automated edits inspectable through preview, diff, and recovery artifacts.

## Quickstart

```bash
python -m podcast_auto_editor probe input.wav --out runs
python -m podcast_auto_editor run input.wav --out runs
```

FFmpeg/ffprobe are used for real media probing/rendering when installed. Core timeline, safety policy, artifact, subtitle, and chapter logic are pure Python stdlib and tested without external services.

## Safety policy

Speech/retake edits default to `proposed`. Auto-accept requires `auto_low_risk_speech = true`, confidence `>= 0.90`, low risk, evidence, and preview/diff/recovery artifacts. Ambiguous, overlapping, meaning-changing, censorship-like, or low-confidence edits are never auto-accepted.

For intentional human-reviewed retake removal, use the explicit review path:

```bash
python -m podcast_auto_editor review-accept runs/episode/timeline.proposed.v1.json \
  --operation-id retake_abc123 \
  --reviewer producer \
  --note "Confirmed duplicate intro" \
  --out runs/episode/timeline.reviewed.v1.json
```

Plain `accept` is still insufficient for rendering accepted `retake_cut` operations; render requires either successful auto-accept provenance or explicit manual-review provenance.
