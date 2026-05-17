# Real Podcast Walkthrough: EP1

繁體中文說明見本文件下方「繁體中文」段落。

## Goal

Run the Stage 1 PR-A2 walkthrough against a real recorded WAV while keeping the same offline/mock defaults as `quickstart`. This proves the pipeline can ingest real audio and produce the review-session, recipe, and AI-draft artifacts without committing private media.

Real ASR, alignment, and diarization provider execution is deferred to X2.1, X3.1, and X4.1.

## Input

Use a local WAV file. For the EP1 smoke test, the expected mounted file is:

```bash
/media/ma/1AF83466F83441F5/startup/ep1-test-soundtrack-20260429/Untitled_1 #06.wav
```

Do not commit files from `/media/`.

## End-to-end command

```bash
bash scripts/walkthrough-real-podcast.sh \
  --audio "/media/ma/1AF83466F83441F5/startup/ep1-test-soundtrack-20260429/Untitled_1 #06.wav"
```

Equivalent direct CLI command:

```bash
uv run python -m podcast_auto_editor quickstart \
  --real-audio "/media/ma/1AF83466F83441F5/startup/ep1-test-soundtrack-20260429/Untitled_1 #06.wav" \
  --out runs/walkthrough \
  --episode-id ep1-real
```

## Expected artifact paths

The script prints these paths:

```text
review-session.json: runs/walkthrough/runs/ep1-real/review-session.json
recipe.v1.json:      runs/walkthrough/runs/ep1-real/recipe.v1.json
ai-draft.v1.json:    runs/walkthrough/runs/ep1-real/ai/ai-draft.v1.json
```

Core run artifacts are under:

```text
runs/walkthrough/runs/ep1-real/timeline.proposed.v1.json
runs/walkthrough/runs/ep1-real/timeline.accepted.v1.json
runs/walkthrough/runs/ep1-real/exports/transcript.json
runs/walkthrough/runs/ep1-real/exports/episode.edited.wav
```

## Expected output shape

Stub transcript excerpt:

```json
{
  "schema_version": "transcript.v1",
  "provider": "stub",
  "segments": [
    {
      "start": 0.0,
      "end": 1.0,
      "text": "Stub transcript for ep1-real"
    }
  ]
}
```

Recipe shape:

```json
{
  "schema_version": "recipe.v1",
  "source_media": {
    "path": "runs/walkthrough/raw/ep1-real.wav",
    "sha256": "...",
    "duration_s": 6.5
  },
  "accepted_timeline": {"schema_version": "timeline.v1"},
  "ai_draft": {"schema_version": "ai-draft.v1"}
}
```

AI draft shape:

```json
{
  "schema_version": "ai-draft.v1",
  "dry_prompt": true,
  "metadata": {
    "source_segment_count": 1,
    "candidate_operation_count": 0
  }
}
```

## Dashboard

Open the local review dashboard after the run:

```bash
uv run python -m podcast_auto_editor review serve runs/walkthrough/runs/ep1-real
```

Default dashboard URL:

```text
http://127.0.0.1:8765
```

## Notes

- `--real-audio` validates that the input exists, is a regular file, and has a `.wav` suffix.
- The input WAV is hardlinked or copied into `runs/walkthrough/raw/ep1-real.wav`; the original `/media/` file is never modified.
- Re-running `scripts/walkthrough-real-podcast.sh` with the same `--out` removes and recreates that output directory.
- The walkthrough intentionally uses the stub transcript provider and dry AI draft mode.

## 繁體中文

這個 walkthrough 是 PR-A2 的真實錄音煙霧測試：用本機 WAV 取代 synthetic fixture，但仍維持離線/mock 預設，不啟用真實 ASR、alignment、diarization 或 hosted AI。

執行：

```bash
bash scripts/walkthrough-real-podcast.sh \
  --audio "/media/ma/1AF83466F83441F5/startup/ep1-test-soundtrack-20260429/Untitled_1 #06.wav"
```

完成後檢查：

```text
runs/walkthrough/runs/ep1-real/review-session.json
runs/walkthrough/runs/ep1-real/recipe.v1.json
runs/walkthrough/runs/ep1-real/ai/ai-draft.v1.json
```

開啟 dashboard：

```bash
uv run python -m podcast_auto_editor review serve runs/walkthrough/runs/ep1-real
```

預設網址是 `http://127.0.0.1:8765`。真實 ASR、alignment、diarization 驗證分別延後到 X2.1、X3.1、X4.1。
