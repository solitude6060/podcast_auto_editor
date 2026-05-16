from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "speaker_segments.v1"


class DiarizationError(Exception):
    """Raised when diarization input / output is invalid."""


class DiarizationProviderError(DiarizationError):
    """Raised when a diarization provider cannot run.

    Common reasons: a required dependency (e.g. ``pyannote-audio``) is not
    installed, an authentication token is missing, or a real-model
    integration has not yet been wired in.
    """


def _coerce_seconds(value: Any, field: str, idx: int) -> float:
    if value is None:
        raise DiarizationError(f"segment[{idx}].{field} is required")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise DiarizationError(f"segment[{idx}].{field} must be numeric: {value!r}") from exc


def _coerce_confidence(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        c = float(value)
    except (TypeError, ValueError):
        return 0.0
    if c < 0.0:
        return 0.0
    if c > 1.0:
        return 1.0
    return c


def normalize_speaker_segments(raw: list[Any]) -> list[dict[str, Any]]:
    """Validate + normalize diarization segments into the canonical shape.

    Each segment must carry numeric ``start`` / ``end`` (with end > start)
    and a non-empty ``speaker_id`` string. ``confidence`` is clamped to
    ``[0.0, 1.0]``; missing or non-numeric confidence becomes 0.0. Extra
    fields are preserved so per-show metadata can flow through.
    """
    out: list[dict[str, Any]] = []
    for idx, raw_seg in enumerate(raw):
        if not isinstance(raw_seg, dict):
            raise DiarizationError(f"segment[{idx}] must be an object")
        if "start" not in raw_seg:
            raise DiarizationError(f"segment[{idx}].start is required")
        if "end" not in raw_seg:
            raise DiarizationError(f"segment[{idx}].end is required")
        if "speaker_id" not in raw_seg:
            raise DiarizationError(f"segment[{idx}].speaker_id is required")
        start = _coerce_seconds(raw_seg["start"], "start", idx)
        end = _coerce_seconds(raw_seg["end"], "end", idx)
        if end <= start:
            raise DiarizationError(f"segment[{idx}].end must be after start")
        speaker_id = raw_seg["speaker_id"]
        if not isinstance(speaker_id, str) or not speaker_id.strip():
            raise DiarizationError(f"segment[{idx}].speaker_id must be a non-empty string")
        segment = dict(raw_seg)
        segment["start"] = start
        segment["end"] = end
        segment["speaker_id"] = speaker_id
        segment["confidence"] = _coerce_confidence(raw_seg.get("confidence"))
        out.append(segment)
    return out


class DiarizationProvider(ABC):
    """Pluggable diarization provider contract.

    Implementations take an audio path and return a list of validated
    speaker segments. The mock provider (offline, no network) ships in
    PR-C; the real pyannote adapter is reserved for a follow-up once a
    HuggingFace token + real recording are available.
    """

    @abstractmethod
    def diarize(self, audio_path: str | Path, **options: Any) -> list[dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError


class MockDiarizationProvider(DiarizationProvider):
    """Offline diarization provider that reads segments from a JSON config.

    Used in CI and on developer machines that do not have access to the
    real pyannote pipeline. The config JSON shape is
    ``{"segments": [{"start": ..., "end": ..., "speaker_id": ..., "confidence": ...}, ...]}``.
    When no config is provided the provider returns an empty segment list
    so downstream code can treat the audio as single-speaker.
    """

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path: str | Path | None = config_path

    def diarize(self, audio_path: str | Path, **options: Any) -> list[dict[str, Any]]:  # noqa: ARG002
        if self.config_path is None:
            return []
        data = json.loads(Path(self.config_path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise DiarizationError("mock diarization config must be a JSON object")
        segments = data.get("segments", [])
        if not isinstance(segments, list):
            raise DiarizationError("mock diarization config `segments` must be a list")
        return normalize_speaker_segments(segments)


class PyannoteDiarizationProvider(DiarizationProvider):
    """Lazy-import adapter for the pyannote-audio speaker diarization pipeline.

    Real model integration is deferred to PR-C2 (requires HuggingFace
    token + a real recording for accuracy verification). This adapter
    currently raises a clear ``DiarizationProviderError`` that distinguishes
    "dependency missing" from "integration deferred" so users know how to
    proceed.
    """

    def diarize(self, audio_path: str | Path, **options: Any) -> list[dict[str, Any]]:  # noqa: ARG002
        try:
            import pyannote.audio  # noqa: F401
        except ImportError as exc:
            raise DiarizationProviderError(
                "pyannote-audio is not installed; run `uv add pyannote-audio` and set "
                "HF_TOKEN to enable real diarization. Use `--provider mock` to ship without "
                "the heavy dependency."
            ) from exc
        raise DiarizationProviderError(
            "pyannote real-model integration is deferred to follow-up PR-C2; use `--provider mock` "
            "for now. PR-C2 will wire the pyannote/speaker-diarization-3.1 pipeline once a real "
            "2-speaker fixture is available for accuracy verification."
        )


def diarize_to_file(
    audio_path: str | Path,
    out_path: str | Path,
    *,
    provider: str = "mock",
    config_path: str | Path | None = None,
) -> Path:
    """Drive a diarization provider and write the canonical artefact.

    The artefact shape is ``{"schema_version": "speaker_segments.v1",
    "audio_path": "<source>", "segments": [...]}``. Caller-side validation
    happens before the artefact is written, so a failed provider call
    leaves no half-written file on disk.
    """
    if provider == "mock":
        prov: DiarizationProvider = MockDiarizationProvider(config_path=config_path)
    elif provider == "pyannote":
        prov = PyannoteDiarizationProvider()
    else:
        raise DiarizationError(f"unknown provider: {provider!r} (expected one of: mock, pyannote)")

    segments = prov.diarize(audio_path)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "audio_path": str(audio_path),
        "segments": segments,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return out
