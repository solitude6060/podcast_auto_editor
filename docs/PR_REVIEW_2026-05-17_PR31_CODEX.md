# PR #31 — Codex code review

- PR URL: https://github.com/solitude6060/podcast_auto_editor/pull/31
- Base: `dev` → Head: `pr-c/diarization-cli`
- Head SHA: `a1d4cf0`
- Review date: 2026-05-17
- Reviewer: Codex (gpt-5.x via codex CLI) invoked as `codex:codex-rescue` subagent
- Verdict: **REQUEST CHANGES**

## Findings

### MEDIUM
- **`podcast_auto_editor/diarization.py:24`** — `_coerce_seconds` converts any `float(value)` result without rejecting negative, `NaN`, `inf`, or boolean inputs. `normalize_speaker_segments` only checks `end > start` (line 67), so segments like `{"start": -5, "end": 1, "speaker_id": "spk0"}` or `{"start": float("nan"), ...}` can be written into `speaker_segments.v1.json`. **Disposition: Fixed in fix round** — mirror transcript validation (reject bool, None, non-finite numbers, negative start).

### LOW
- **`docs/plans/2026-05-17-persona-ab-stage1-execution.md:217`** — The plan called for a README "Diarization (optional)" section mirrored to zh-TW; PR-C did not add it. **Disposition: Fixed in fix round** — README + zh-TW section added.

## Risk callouts (confirmed clean)
- **Lazy import:** the only `pyannote` reference is inside `PyannoteDiarizationProvider.diarize` (line 132). Top-level module load does not import `pyannote-audio`.
- **Atomic write safety:** `diarize_to_file` calls `prov.diarize` before `mkdir` / `write_text`, so a provider exception leaves no half-written artefact.
- **Downstream cue-dict compatibility:** SRT/VTT/chapter consumers access only `start`/`end`/`text`. Adding optional `speaker_id` does not break them.
- **CLI eager import:** `cli.py` imports only `.diarization` symbols at line 24; that module's pyannote import remains lazy.
- **Non-monotonic / overlapping segments:** intentional design choice — overlapping speaker turns are valid output from real diarization. Not a bug.

## What was confirmed clean
Pyannote lazy import, CLI routing, malformed/non-object segment rejection in mock config, provider-failure no-write path, optional `speaker_id` preservation in transcript cue dicts, and all downstream SRT/VTT/chapter cue consumers.
