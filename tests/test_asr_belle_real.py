"""
Belle real-load integration tests — env-gated, skipped by default in CI.

These tests are NOT a duplicate of
``test_faster_whisper_provider_accepts_belle_whisper_zh_drop_in`` in
``tests/test_asr.py``, which only verifies that the model-id string is passed
through unchanged to ``WhisperModel.__init__`` (a pure mock).

What these tests add:
- Verify that ``transcribe_to_file`` produces a well-formed ``transcript.v1``
  payload with ``provider == "faster-whisper-local"`` and
  ``model == "BELLE-2/Belle-whisper-large-v3-zh"`` when given a real or
  operator-supplied audio file.
- Verify that ``len(segments) >= 1`` and at least one segment has non-empty
  ``text`` — i.e. the decoder ran and produced output, not just that the
  constructor accepted the model id.

Env variables:
  PAE_BELLE_REAL=1                  — opt-in gate (required to run gated test)
  PAE_BELLE_REAL_AUDIO=<path>       — path to a short (~5-10s) WAV file
  PAE_BELLE_REAL_DEVICE=cuda        — override device (default: cuda)
  PAE_BELLE_REAL_COMPUTE=float16    — override compute_type (default: float16)

Typical invocation:
  PAE_BELLE_REAL=1 PAE_BELLE_REAL_AUDIO=/path/to/zh_sample.wav \\
      uv run --group dev pytest tests/test_asr_belle_real.py -v
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import podcast_auto_editor.cli as cli

# ---------------------------------------------------------------------------
# Env-gated real-load test
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not os.environ.get("PAE_BELLE_REAL"),
    reason="PAE_BELLE_REAL is not set",
)
def test_belle_real_load_and_transcribe_when_opted_in(tmp_path):
    """PR-X2.1: With PAE_BELLE_REAL=1, load Belle-whisper-large-v3-zh and
    transcribe the operator-supplied audio file.

    Asserts:
    - Written JSON is a transcript.v1 payload.
    - provider == "faster-whisper-local".
    - model == "BELLE-2/Belle-whisper-large-v3-zh".
    - At least one segment with non-empty text (decoder ran; does NOT assert
      specific Chinese characters to avoid fragility).
    """
    pytest.importorskip("faster_whisper")

    audio_path_str = os.environ.get("PAE_BELLE_REAL_AUDIO", "")
    if not audio_path_str:
        pytest.skip(
            "PAE_BELLE_REAL_AUDIO is not set; "
            "supply a path to a short Chinese WAV to run this test"
        )
    audio_path = Path(audio_path_str)
    if not audio_path.is_file():
        pytest.skip(
            f"PAE_BELLE_REAL_AUDIO={audio_path_str!r} does not exist or is not a file"
        )

    out_path = tmp_path / "transcript.json"

    cli.transcribe_to_file(
        audio_path,
        out_path,
        provider_name="faster-whisper-local",
        model="BELLE-2/Belle-whisper-large-v3-zh",
        device=os.environ.get("PAE_BELLE_REAL_DEVICE", "cuda"),
        compute_type=os.environ.get("PAE_BELLE_REAL_COMPUTE", "float16"),
    )

    assert out_path.is_file(), "transcribe_to_file must write the output file"
    data = json.loads(out_path.read_text(encoding="utf-8"))

    assert data.get("schema_version") == "transcript.v1"
    assert data.get("provider") == "faster-whisper-local"
    assert data.get("model") == "BELLE-2/Belle-whisper-large-v3-zh"

    segments = data.get("segments", [])
    assert len(segments) >= 1, "Transcript must contain at least one segment"
    assert any(
        seg.get("text", "").strip() for seg in segments
    ), "At least one segment must have non-empty text"


# ---------------------------------------------------------------------------
# Always-on: confirms the module imports clean and collection works without
# faster-whisper installed (the gated test above is skipped by the mark).
# ---------------------------------------------------------------------------


def test_belle_real_test_skips_cleanly_when_opted_out():
    """PR-X2.1: This test always passes to confirm the module collects without
    errors on machines that have neither faster-whisper installed nor
    PAE_BELLE_REAL set.  The gated test above is skipped by its skipif mark;
    this companion test exists so pytest -v output shows the module is healthy.
    """
    assert True
