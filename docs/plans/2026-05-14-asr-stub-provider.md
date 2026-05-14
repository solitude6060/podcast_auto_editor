# Optional local ASR adapter stub

## Goal
Implement advanced roadmap Phase A3 with a dependency-free ASR provider boundary and deterministic stub provider so transcript generation can be exercised without cloud services or mandatory ASR dependencies.

## Scope
- Add `podcast_auto_editor/asr.py` with a transcript provider protocol and provider registry.
- Add `transcribe <input> --provider stub --out <transcript.json>` CLI command.
- Validate provider output through the existing transcript validation path before writing.
- Keep provider failures side-effect safe: failed transcription must not write or mutate media artifacts.
- Document English and Traditional Chinese usage.

## Acceptance criteria
- Core tests pass without ASR dependencies.
- Stub provider writes `transcript.v1` JSON with normalized segments.
- Invalid provider output fails clearly and does not write the output file.
- Unknown providers fail with an actionable CLI message.
