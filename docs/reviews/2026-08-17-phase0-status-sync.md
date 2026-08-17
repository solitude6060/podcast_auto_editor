# Review: `docs/2026-08-17-status-sync`

Traditional Chinese: [`2026-08-17-phase0-status-sync.zh-TW.md`](2026-08-17-phase0-status-sync.zh-TW.md)

**Date:** 2026-08-17  
**Range:** `dev` `2c9a81d` … `db56c26`  
**Branch:** `docs/2026-08-17-status-sync`  
**Lanes:** orchestrator verification of the full diff; independent [code-reviewer](157218d4-8c7a-44a1-aa47-35d66528648b) and [architect](29159c8c-0251-4f82-86cd-dd40f0348eee) lanes were dispatched on the same range.

## What landed

| Commit | Subject |
|---|---|
| `86d9560` | Skip CUDA `.to` when the pyannote pipeline has no `.to` |
| `08a165b` | Two-pass loudnorm, lossy true-peak retries, per-profile reports |
| `21e68ba` | README / SDD / `user_todo` / 2026-08-17 status sync |
| `db56c26` | Record Phase 0 hashes |

Working tree at review time: clean except untracked `.claude/` and `.omc/`.

## Strengths

- CUDA host crash has a forced-`is_available` regression, so CPU CI can catch it.
- Two-pass loudnorm and lossy margin retries have direct tests in `tests/test_media_sync.py` and `tests/test_exports.py`.
- MiniMax key is read from the environment and the draft test asserts it is not serialized.
- README comparison table now includes `auto-editor`, marks `recipe.v1` implemented, and states denoise is not shipped.

## Triage

| ID | Finding | Severity | Risk? | This PR? | Why |
|---|---|---|---|---|---|
| F1 | Top-level `quality_gate_report` stays the first profile after a later profile fails | HIGH | Yes | Yes | Contradicts `docs/plans/2026-05-18-podcaster-ready-ai-mvp.md` (“avoid ambiguous partial-success metadata”). CLI markdown can print `Quality gate: True` while `podcast-stereo` failed. Locked in by `tests/test_exports.py` and `tests/test_cli.py`. |
| F2 | Failed export metadata is only on the in-memory timeline | HIGH | Yes | Yes | `cli.py` `render` / `run` do not write `timeline.accepted.v1.json` on `MediaToolError`. Producer `report` / HTML read the file, so the new fields never appear on the failure path that motivated the patch. |
| F3 | `test_generate_ai_draft_normalizes_live_response` dropped `operation_explanations[0].operation_known` | LOW | Low | Yes | Accidental assertion deletion in the same hunk as the MiniMax test. Restore. |
| F4 | Incomplete loudnorm JSON raises `KeyError` | LOW | Low | No | Same `json.loads` + required-key pattern as pre-existing `measure_audio_quality`. |
| F5 | SDD quality-gate section omits two-pass loudnorm and lossy retries | MEDIUM | Docs drift | Yes | Spec/code disagree after `08a165b`. Docs update, not a product bug. |

## Findings

### F1 — `podcast_auto_editor/pipeline.py:384`

On each profile, the code writes `export_metadata["quality_gate_report"] = export_profiles[0]["quality_gate_report"]`. If `podcast-stereo` fails after `archive-wav` passed, the top-level gate is still the passing archive report. `failed_quality_profile` is set, but `_build_run_report` and `build_html_report` still surface `quality_gate_report.passed` as the headline.

### F2 — `podcast_auto_editor/cli.py:626-632` and `pipeline.py:478-480`

`render()` mutates the timeline then raises. `main` `render` only catches `ValueError`. `run_pipeline` does not catch `MediaToolError` (only `quickstart` does). The accepted timeline is written only after a successful return, so `report` cannot name the failed profile from disk.

### F3 — `tests/test_ai_drafts.py:130`

The live-response normalization test no longer asserts `operation_explanations[0]["operation_known"] is True`.

## Architectural status

**WATCH.** Mixing the 2026-05-18 quality behavior with 2026-08-17 docs on one branch is an intentional Phase 0 choice, not a merge blocker. The WATCH is the top-level quality-gate contract: headline `passed` can disagree with a later profile.

## Synthesis

- code-reviewer recommendation: **REQUEST CHANGES** (F1, F2)
- architect status: **WATCH**
- final recommendation: **REQUEST CHANGES**

## Verification at review time

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider
# 314 passed, 11 skipped (2026-08-17, tip db56c26)
```
