# PR-X3.1 WhisperX triple-review fix log

## Review inputs found

- `/tmp/pr46_review_gemini.out` (review starts at line 578): REQUEST CHANGES. High finding: `WhisperXAlignmentProvider.align()` passes `audio_path` directly to `whisperx.align()` instead of loading audio with `whisperx.load_audio()`. Medium finding: whitespace or empty WhisperX word text should be filtered before normalization. Low finding: explicitly passing `interpolate_method="nearest"` should be considered if missing timestamps are common.
- `/tmp/pr46_review_minimax.out`: BLOCK. Critical finding 1 matches Gemini: `whisperx.align()` receives a path string instead of a loaded numpy audio array. Critical finding 2 argued that `model_name=<local path>` may trigger Hugging Face download and should be verified against source. High finding: CUDA alignment model cleanup should call `torch.cuda.empty_cache()` after use. Medium findings: runbook commands need concrete latency and network-isolation checks; real test schema assertions are thin.
- `/tmp/pr46_review_codex.out` (review starts at line 2543): REQUEST CHANGES. High finding: load audio explicitly before `whisperx.align()`. High finding: flattening only handles `segments[*].words[*].word`, missing `word_segments` and `text` alternatives. Medium finding: define and pin zero-duration / overlapping word policy. Medium finding: add fake-module always-on tests for API call shape and output mapping. Low findings: stale "deferred to PR-X3.1" text and falsey `model_path` kwarg falling back to env.

No PR #46-specific review archive was found under `docs/fix-logs/` or `.omc/` in this worktree. Git history showed PR-X3.1 commits on `feature/pr-x3-1-whisperx-plan` and earlier PR #43-45 review archives, but no existing PR #46 fix log.

## WhisperX source verification

Source checked: upstream `m-bain/whisperX` `whisperx/alignment.py` on GitHub main.

Relevant signature at source lines 1451-1452:

```python
def load_align_model(language_code: str, device: str, model_name: Optional[str] = None, model_dir=None, model_cache_only: bool = False):
```

Relevant Hugging Face loader calls at source lines 1489-1491:

```python
processor = Wav2Vec2Processor.from_pretrained(model_name, cache_dir=model_dir, local_files_only=model_cache_only)
align_model = Wav2Vec2ForCTC.from_pretrained(model_name, cache_dir=model_dir, local_files_only=model_cache_only)
```

Relevant align signature at source lines 1511-1530:

```python
def align(transcript, model, align_model_metadata, audio, device, ...)
```

Conclusion:

- `device` is the second positional parameter and can also be passed as a keyword argument.
- `model_name` is forwarded directly to Transformers `from_pretrained()`. Transformers accepts either a Hugging Face model id or a local directory path, so MiniMax's "local path always means HF id" claim is not strictly correct.
- The reviewer concern about accidental network access is still valid because WhisperX exposes `model_cache_only`, which maps to Transformers `local_files_only`. The provider should pass `model_cache_only=True` when loading a prevalidated local model path.
- `whisperx.align()` accepts an `audio` object, not a model path. The provider must call `whisperx.load_audio(str(audio_path))` and pass that returned array into `whisperx.align()`.

## Fix plan

1. Add fake-module tests that fail on the current provider:
   - `whisperx.load_audio()` must be called with the audio path.
   - The exact loaded audio object must be positional argument 4 to `whisperx.align()`.
   - `load_align_model()` must receive `model_cache_only=True`.
   - Output mapping must support `word_segments`, `text`, empty-word filtering, and preserve zero-duration / overlapping words.
2. Apply the minimal provider change:
   - Preserve explicit `model_path` precedence over env even for falsey kwargs.
   - Pass `model_cache_only=True` to `load_align_model()`.
   - Load audio before calling `align()`.
   - Free CUDA cache in a `finally` block after model use.
   - Flatten `segments[*].words` with fallback to `word_segments`; use `word` or `text`; drop empty text; keep zero-duration and overlapping words intentionally.
3. Update stale provider/CLI text and runbook commands.
