# 2026-05-17 — PR-A: Synthetic-episode end-to-end walkthrough

Scope: PR-A from `docs/plans/2026-05-17-persona-ab-stage1.md`.

Original plan goal: "Real-podcast end-to-end run + fix-log (verify foundation before building on it)."

Adjustment: a real-podcast pass requires audio I do not have rights to commit. This walkthrough drives the entire CLI surface against the existing synthetic `demo-fixtures` material, captures every observable, lists gaps that genuinely need a real recording (so the user can decide what to provide later), and folds the one workflow-blocker bug it found into this PR with a regression test.

## Walkthrough commands and observed results

Executed on branch `pra/real-podcast-e2e-walkthrough` from dev SHA `29693d7`.

| # | Step | Command | Result |
|---|---|---|---|
| 1 | Generate fixtures | `podcast-auto-editor demo-fixtures --out /tmp/pae-e2e-walk/media` | `demo-silence.wav` (353 KB, 4 s) + `demo-av.mp4` (13 KB). Silence-only audio; no speech content. |
| 2 | Full run | `podcast-auto-editor run /tmp/pae-e2e-walk/media/demo-silence.wav --out /tmp/pae-e2e-walk/runs/ep1 --episode-id ep1` | 20 artefacts under `runs/ep1/ep1/` including `timeline.proposed.v1.json`, `timeline.accepted.v1.json`, exports (`episode.edited.wav`, mono/stereo MP3, subtitles, chapters, transcript), preview, diff, recovery. **Friction:** the `--out` path was interpreted as a parent dir and `--episode-id ep1` nested another `ep1/` underneath, producing `runs/ep1/ep1/...` — surprising for first-time users. |
| 3 | `validate` | `validate /tmp/.../timeline.proposed.v1.json` | `ok`. |
| 4 | `validate-run` | `validate-run --timeline /tmp/.../timeline.proposed.v1.json` | `ok: timeline; duration: 4s`. |
| 5 | `report` (markdown + JSON) | `report /tmp/.../ep1` | 1 proposed + 1 accepted silence_cut, risk=`deterministic`, detector=`ffmpeg.silencedetect`. Same operation in both counters because `run` auto-accepts deterministic silence; this is correct per the safety policy but the rendered report does not visually distinguish "the same op appears in both states". |
| 6 | `review-list` | `review-list /tmp/.../timeline.proposed.v1.json --format markdown` | Single-row table for `silence_aaeb987ee524`. |
| 7 | `html-report` | `html-report /tmp/.../ep1 --out /tmp/.../report.html` | 2 405 bytes, opens locally. |
| 8 | `ai draft --dry-prompt` | `ai draft --timeline ... --transcript-json synthetic.json --dry-prompt --out .../ai-draft.v1.json` | 1 888 byte artefact with `schema_version: ai-draft.v1`, `dry_prompt: true`, base_url + model echoed. `candidate_operation_count: 0` (correct — only `retake_cut` / `speech_cut` are AI candidates; this run has only deterministic silence). |
| 9 | `explain --with-ai --dry-prompt` | `explain /tmp/.../timeline.proposed.v1.json --operation-id <id> --with-ai --dry-prompt --format json` | Returns full payload with `operation_id`, `risk`, `base_explanation`, `ai_explanation.dry_prompt = true`. **First-attempt friction:** I initially tried `--timeline X` (matching the `ai draft` shape); `explain` takes timeline as a positional argument. README's example is correct (positional) but the inconsistency with `ai draft`'s `--timeline` flag tripped the walkthrough. |
| 10 | `review serve` (probe only) | `load_review_context` + `build_launcher_script` + `build_review_app_html` exercised in-process | status keys + `ai_draft` populated correctly; next pending operation surfaced with full decision commands; HTML 4 076 bytes including the new "Artifacts" section. Server bound to 127.0.0.1 only. |
| 11 | `dry-run` | `dry-run /tmp/.../demo-silence.wav --out /tmp/.../runs/dry --episode-id ep1` | No `exports/episode.edited.wav` / mp3 (correctly skipped); text exports (subtitles, chapters, transcript), diff, preview, recovery, both timelines all produced. Behaviour matches SDD §"dry-run writes inspection artifacts without edited media exports". |
| 12 | `review next` | `review next /tmp/.../review-session.json --timeline /tmp/.../timeline.proposed.v1.json` | **Failed — `FileNotFoundError` for `review-session.json`.** The `run` command does not seed an empty session file; the dashboard's `load_review_context` handles this case (`if session_path.exists() else {empty session}`), but the CLI's `review next` / `status` / `decide` raise on missing file. The documented `run → review next → review decide` flow is broken on first invocation. **Fix folded into this PR — see "Fix bundled with PR-A" below.** |
| 13 | `recipe export` | `recipe --help` | Command does not exist. Expected — `recipe export/import` is PR-G in `docs/plans/2026-05-17-persona-ab-stage1.md`. |

## Fix bundled with PR-A

PR-A's plan exit criterion says "fix only blocking ones in this PR (others become follow-up issues)". Finding #12 is the one workflow blocker found, and the fix is surgical (≤ 20 lines + test):

- `podcast_auto_editor/cli.py` — introduce `_load_review_session_or_empty(session_path, timeline_path)` mirroring `local_review_server.load_review_context`'s default-empty pattern; apply in `review next`, `review status`, and `review decide`.
- `tests/test_cli.py` — regression test that runs `review next` against a freshly-completed `run` directory (with no `review-session.json`) and asserts a non-empty pending item is printed instead of a traceback.

Rejected alternative: have `run` write an initial empty `review-session.json`. The dashboard already handles missing-session gracefully, so the canonical fix is to keep the missing-file path supported uniformly across CLI + dashboard.

## Gaps that genuinely need real podcast material (deferred to follow-up)

These are real verification gaps that synthetic silence cannot exercise. Listed so a single real-podcast run later (user-supplied or CC-licensed) can close them in one pass:

1. **Speech-cut / retake-cut detection true-positive rate.** The walkthrough produced zero AI candidates because the fixture is silence-only.
2. **AI draft chapter / show-notes / summary quality.** `--dry-prompt` confirms the request shape; only a live LLM run with real transcript can judge usefulness.
3. **Filler / backchannel detection on real speech.** Stage 1 PR-E target.
4. **Real-noise denoise / loudness leveler audibility.** Synthetic silence trivially hits LUFS targets.
5. **Diarization accuracy on a 2-speaker interview** — Stage 1 PR-C target; depends on `pyannote-audio` / `WhisperX` choice.
6. **Live Docker GPU + Ollama model download path** — `scripts/e2e-docker-ai-stack.sh` is regression-tested with a stub; live runtime behaviour still depends on host availability and installed models.
7. **MP4 sync gate** under realistic frame rates / variable audio drift.

## Minor UX observations (logged, not fixed in this PR per surgical-changes)

- `run --out runs/ep1 --episode-id ep1` produces `runs/ep1/ep1/` nesting. Either document that `--out` is a parent, or have `--out` accept a leaf path when `--episode-id` is supplied. Follow-up.
- `explain` uses a positional `timeline` argument while `ai draft` uses `--timeline`. Pick one across the CLI for consistency. Follow-up.
- `report`'s "Proposed edits: 1, Accepted edits: 1" reads as double-counting until the reader recognises that the same operation appears in two timeline files. A one-line note in the report header would help. Follow-up.

## Verification gate

Run on the fix branch after the bundled fix lands:

- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider`
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run python -m compileall -q podcast_auto_editor tests`
- `UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor ./scripts/smoke.sh`
- `git ls-files .omx` → empty.

## Decision triggers for the rest of Stage 1

- If a real episode is provided, repeat steps 1-13 against it and append the results as a new fix-log dated by the run. This will likely surface additional bugs that synthetic silence cannot.
- If no real episode is provided in the next session, proceed to PR-H (README messaging) since it has no real-audio dependency.
