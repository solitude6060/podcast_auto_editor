# Podcast Auto Editor — project status review

Traditional Chinese: [`2026-08-17-project-status-review.zh-TW.md`](2026-08-17-project-status-review.zh-TW.md)

**Review date:** 2026-08-17  
**Branch:** `dev` at `2c9a81d` (2026-05-18 20:07 +0800, merge PR #48)  
**Working tree:** dirty — 17 tracked files, +383/−15, plus untracked `.claude/`, `.omc/`, and 2026-05-18 podcaster-ready docs  
**Last commit age:** 91 days as of 2026-08-17

**Phase 0 addendum (same day):** Hygiene landed on `docs/2026-08-17-status-sync`. README now marks `recipe.v1` implemented and pyannote as runnable when optional deps exist. The 2026-05-18 quality patch is `08a165b`. The CUDA `.to` guard is `86d9560`. Working-tree dirt from that patch is no longer current. Test collect count after the new regression: 325 (314 passed, 11 skipped on this host).

---

## 1. Progress snapshot

```
CLI contract        done
timeline.v1 / undo  done
dry-run + report    done
review helper + UI  done (localhost)
recipe.v1           done (README still says "planned")
ASR adapters        done (default remains stub)
pyannote adapter    done (README still says follow-up)
real-episode proof  not done (stub walkthrough; audio disk unmounted)
1.0 release         blocked on user sign-off since 2026-05-18; not recommended
```

Persona Stage 1 PRs A–H and X1–X4.1 landed on `dev` in mid-May 2026. The remaining gap is not another provider. It is a real episode through real ASR, human review, and a publish-quality export.

---

## 2. Code statistics

Measured 2026-08-17 on the dirty `dev` worktree.

| Metric | Value | How measured |
|---|---|---|
| Package modules | 27 `.py` files under `podcast_auto_editor/` | `find podcast_auto_editor -name '*.py'` |
| Source lines | 6,141 | `wc` over `podcast_auto_editor/*.py` |
| Test files | 36 | `tests/test_*.py` |
| Test lines | 6,642 | `wc` over those files |
| Tests collected | 324 | `uv run --group dev pytest --collect-only -q` |
| Tracked Markdown | 161 | `git ls-files '*.md'` |
| `dev` ahead of `main` | 40 commits | `git log --oneline main..dev` |
| `main` HEAD | `ae3ec41` 2026-05-18 01:05 +0800 | `git log -1 main` |
| Locked worktrees | 19 under `.claude/worktrees/` | `git worktree list` |

`cli.py` is 1,092 lines / 54,069 bytes. It is the largest module.

---

## 3. What exists (verified)

### Core

- Canonical `timeline.v1` with proposed / accepted / rejected operations, recovery map, provenance (`podcast_auto_editor/timeline.py`).
- Safety policy: speech/retake/backchannel stay proposed; render needs review or auto-accept provenance (`docs/sdd/podcast-auto-editor-mvp.md`, `cli.py`).
- Silence proposals via ffmpeg `silencedetect` (`silence.py`, `media.py`).
- Heuristic `speech_cut` / `retake_cut` / `backchannel_cut` (`retake.py`).
- Export profiles: archive WAV, podcast stereo/mono MP3, LUFS / true-peak / clip gates (`exports.py`, `quality.py`).
- `recipe export` / `recipe apply` with source sha256 (`recipe.py`). README comparison table still marks this as planned (`README.md:21`).

### Interfaces (roadmap UI-1–UI-4)

| Layer | Status | Evidence |
|---|---|---|
| CLI | present | `cli.py` `build_parser()` |
| Static HTML report | present | `html-report`, `html_report.py` |
| Text review helper | present | `review next/status/decide/rebuild` |
| Localhost UI | present | `review serve` on `127.0.0.1` |
| Desktop wrapper | launcher only | `review launcher` writes `.desktop`; no packaged app |

### AI / ML

| Path | Default | Real path |
|---|---|---|
| ASR | `stub` | `faster-whisper-local`, `whisper-cpp-local`, `qwen3-asr-local` |
| Diarization | `mock` | `pyannote` (lazy import; needs `HF_TOKEN`) |
| Alignment | `mock` | WhisperX when deps present; Lattifai decode blocked |
| AI draft | `--dry-prompt` in quickstart | OpenAI-compatible HTTP when not dry |

`run_pipeline` still writes `exports/transcript.json` with `"source": "post-edit-stub"` (`pipeline.py:438-448`). That is a different shape from ASR `transcript.v1`.

---

## 4. Spec vs code drift

| Claim | File | Reality |
|---|---|---|
| Recipe "yes (planned)" | `README.md:21` | Implemented on `dev` |
| "Real ASR providers should be added later" | `README.md` transcript section | Four providers registered |
| pyannote "follow-up PR" | `README.md` diarization section | `PyannoteDiarizationProvider.diarize()` exists |
| SDD "29 passed" | `docs/sdd/podcast-auto-editor-mvp.md:72` | 324 collected |
| May survey matrix: denoise "+ (RNNoise/Demucs)" for this tool | `docs/research/2026-05-17-competitor-landscape.md` | No denoise code |
| PR-A "recipe command does not exist" | `docs/fix-logs/2026-05-17-real-episode-e2e.md:27` | Historical; command exists now |

---

## 5. Git and hygiene

| Item | State |
|---|---|
| `dev` vs `origin/dev` | in sync at `2c9a81d` before counting the dirty tree |
| `main` | 40 commits behind `dev`; last promotion was PR #37 (2026-05-16) plus later `main` fix `ae3ec41` |
| Uncommitted product work | loudness / report / dashboard edits matching `docs/plans/2026-05-18-podcaster-ready-ai-mvp.md` |
| `user_todo.md` | still waiting for 1.0 date, 1.1 defer list, branch preference |
| Real walkthrough audio | `/media/ma/1AF83466F83441F5/...` — **disk not mounted** on 2026-08-17 |
| Worktrees | 19 locked trees inside the repo under `.claude/worktrees/`. Persistent-workspace policy wants sibling directories. Do not delete without an explicit request. |
| `.omc/`, `.claude/` | untracked; must stay untracked |

---

## 6. Blockers (ordered by decision impact)

### P0 — evidence, not features

A real spoken episode has not completed the path `real ASR → review → quality-gated export`. PR-A used 4 s of synthetic silence (`docs/fix-logs/2026-05-17-real-episode-e2e.md`). PR-A2 added `--real-audio` but kept stub transcript (`docs/walkthroughs/real-podcast-ep1.md`).

Until that run exists, continue / adjust / stop is under-determined.

### P0 — dirty tree

The 2026-05-18 podcaster-ready edits are the last product work and are not on `dev`. They will be lost on a clean checkout.

### P1 — docs lie

README and SDD advertise a smaller or older product than `dev` implements. Comparison table omits `auto-editor`.

### P1 — `main` lag

Forty commits on `dev` never reached `main`. That is a release-process stall, not a feature stall.

### P2 — incomplete providers

Lattifai decode, review `k` = previous operation, macOS/WSL CI. Already listed as 1.1 in `user_todo.md`. Correct to keep deferred.

---

## 7. Risks

| Risk | Level | Note |
|---|---|---|
| Platform completeness displaced evidence | high | 324 tests, 161 markdown files, multiple ASR adapters; zero publishable real-episode log |
| Calling the next tag `1.0.0` | high | Version would mean "providers exist", not "an episode shipped" |
| Competing on silence-cut CLI | high | `auto-editor` has 4,984 stars |
| Competing on text-edit UX | medium | Poddie / Redact / Bowdler already sit there |
| Worktree / `.claude` clutter | medium | 19 locked worktrees inside the project |
| Denoise expectation | medium | May 2026 matrix over-claimed this repo |

---

## 8. Immediate actions

1. Do not bump to `1.0.0` until a real episode is publish-ready or explicitly failed with a fix-log.
2. Decide the fate of the uncommitted 2026-05-18 quality/report patch (commit on a feature branch, or discard after review).
3. Sync README / SDD / comparison table with `dev` and with `docs/research/2026-08-17-competitor-landscape.md`.
4. Run one real Mandarin episode with a non-stub ASR provider. Write `docs/fix-logs/2026-08-XX-real-episode.md`.
5. After that log, pick one wedge only: review UX, loudness, or Chinese ASR quality.

Follow-up plan: `docs/plans/2026-08-17-adjustment-and-next.md`.
