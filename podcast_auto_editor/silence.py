from __future__ import annotations

from typing import Any

from .config import QualityConfig
from .timeline import new_operation_id


def propose_silence_cuts(
    silence_segments: list[dict[str, float]],
    quality: QualityConfig,
    affected_tracks: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Convert detected silence spans to reversible deterministic cut operations."""
    operations: list[dict[str, Any]] = []
    tracks = affected_tracks or ["audio:0"]
    for segment in silence_segments:
        start = float(segment["start"])
        end = float(segment["end"])
        duration = max(0.0, end - start)
        if duration < quality.min_silence_duration_s:
            continue
        cut_start = start + quality.speech_padding_s
        cut_end = end - quality.speech_padding_s
        if cut_end <= cut_start:
            continue
        operations.append(
            {
                "operation_id": new_operation_id("silence"),
                "type": "silence_cut",
                "source_range": {"start": round(cut_start, 6), "end": round(cut_end, 6), "unit": "seconds"},
                "output_range": None,
                "affected_tracks": tracks,
                "state": "proposed",
                "risk": "deterministic",
                "confidence": 1.0,
                "provenance": {
                    "detector": "ffmpeg.silencedetect",
                    "silence_threshold_dbfs": quality.silence_threshold_dbfs,
                    "min_silence_duration_s": quality.min_silence_duration_s,
                    "speech_padding_s": quality.speech_padding_s,
                    "raw_segment": segment,
                },
                "preview_ref": None,
                "diff_ref": None,
                "recovery_ref": None,
            }
        )
    return operations
