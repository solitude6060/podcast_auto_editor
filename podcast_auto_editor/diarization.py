from __future__ import annotations

import json
import math
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
    # bool is a subclass of int; treat it as a type error rather than silently mapping True/False to 1.0/0.0 seconds.
    if isinstance(value, bool):
        raise DiarizationError(f"segment[{idx}].{field} must be numeric, not bool: {value!r}")
    try:
        seconds = float(value)
    except (TypeError, ValueError) as exc:
        raise DiarizationError(f"segment[{idx}].{field} must be numeric: {value!r}") from exc
    if not math.isfinite(seconds):
        raise DiarizationError(f"segment[{idx}].{field} must be a finite number: {value!r}")
    return seconds


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
        if start < 0:
            raise DiarizationError(f"segment[{idx}].start must be >= 0")
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
        config_path = Path(self.config_path)
        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise DiarizationError(f"mock diarization config not readable: {config_path}: {exc}") from exc
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise DiarizationError(f"mock diarization config is not valid JSON: {config_path}: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise DiarizationError("mock diarization config must be a JSON object")
        segments = data.get("segments", [])
        if not isinstance(segments, list):
            raise DiarizationError("mock diarization config `segments` must be a list")
        return normalize_speaker_segments(segments)


class PyannoteDiarizationProvider(DiarizationProvider):
    """Lazy-import adapter for the pyannote/speaker-diarization-3.1 pipeline.

    The pipeline is constructed once per provider instance on the first
    ``diarize()`` call and reused for subsequent calls. ``pyannote.audio``
    and ``torch`` are imported lazily inside ``_load_pipeline()`` so a core
    install of ``podcast_auto_editor`` never pays the heavy ML import cost.

    Authentication uses ``HF_TOKEN`` from the environment only; the project
    code never prompts, persists, prints, or serialises the token value.
    Pyannote's own ``~/.huggingface/token`` lookup is also honoured because
    ``Pipeline.from_pretrained`` reads it internally when ``use_auth_token``
    is ``None``.
    """

    _MODEL_ID = "pyannote/speaker-diarization-3.1"
    _LICENSE_URL = "https://huggingface.co/pyannote/speaker-diarization-3.1"

    def __init__(self) -> None:
        self._pipeline: Any = None

    def _load_pipeline(self) -> Any:
        """Lazily construct and cache the pyannote pipeline.

        Raises ``DiarizationProviderError`` for missing dependency, missing /
        invalid token, and unaccepted model license.
        """
        if self._pipeline is not None:
            return self._pipeline

        import os

        try:
            import pyannote.audio as _pyannote_audio
        except ImportError as exc:
            raise DiarizationProviderError(
                "pyannote.audio is not installed. "
                "Install the optional dependency group with: "
                "uv sync --extra diarize-pyannote  "
                "(or: pip install 'podcast-auto-editor[diarize-pyannote]'). "
                "Then set HF_TOKEN and accept the model license at "
                f"{self._LICENSE_URL}"
            ) from exc

        token = os.environ.get("HF_TOKEN") or None  # None triggers pyannote's own lookup

        try:
            pipeline = _pyannote_audio.Pipeline.from_pretrained(
                self._MODEL_ID,
                use_auth_token=token,
            )
        except Exception as exc:
            # from None: prevent chained traceback from leaking HF_TOKEN if
            # pyannote or huggingface_hub embeds it in the underlying exception text.
            raise DiarizationProviderError(
                f"Failed to load {self._MODEL_ID}. "
                "Either the model license has not been accepted OR HF_TOKEN is "
                "missing / invalid. "
                f"Accept the license and set HF_TOKEN, then re-run. "
                f"See {self._LICENSE_URL} for setup instructions. "
                f"Original error type: {type(exc).__name__}"
            ) from None

        # Optional: move to GPU when available (CPU default for local-first use)
        try:
            import torch

            if torch.cuda.is_available():
                pipeline.to(torch.device("cuda"))
        except ImportError:
            pass  # torch not installed with CUDA; stay on CPU

        self._pipeline = pipeline
        return self._pipeline

    def diarize(self, audio_path: str | Path, **options: Any) -> list[dict[str, Any]]:  # noqa: ARG002
        pipeline = self._load_pipeline()

        annotation = pipeline(str(audio_path))

        raw: list[dict[str, Any]] = []
        for turn, _track, label in annotation.itertracks(yield_label=True):
            raw.append(
                {
                    "start": float(turn.start),
                    "end": float(turn.end),
                    "speaker_id": str(label),
                    "confidence": 0.0,
                }
            )

        return normalize_speaker_segments(raw)


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
