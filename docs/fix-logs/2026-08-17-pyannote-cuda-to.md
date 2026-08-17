# Fix log: pyannote CUDA move on pipelines without `.to`

Date: 2026-08-17  
Branch: `docs/2026-08-17-status-sync`  
Related: Phase 0 hygiene in `docs/plans/2026-08-17-adjustment-and-next.md`

## Finding

On a host where `torch.cuda.is_available()` is true, `PyannoteDiarizationProvider._load_pipeline` called `pipeline.to(torch.device("cuda"))` unconditionally. Test fakes (and any CPU-only pipeline object) have no `.to`, so five existing pyannote tests failed with `AttributeError` during Phase 0 verification. CPU-only CI would not see the failure.

## Repro

```bash
UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor uv run --group dev pytest -q -p no:cacheprovider tests/test_diarization.py
```

Before the fix, on this machine (CUDA present): five tests failed at `pipeline.to(...)`. After the fix: 24 passed, including a new regression that forces `torch.cuda.is_available()` to true and uses a pipeline without `.to`.

## Fix

Call `.to` only when the pipeline object has that method. Do not swallow other exceptions from a real GPU move.

## Tests added

- `tests/test_diarization.py::test_pyannote_skips_cuda_move_when_pipeline_has_no_to`

## Files

- `podcast_auto_editor/diarization.py`
- `tests/test_diarization.py`
- this log
