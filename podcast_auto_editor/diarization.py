from __future__ import annotations

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


class DiarizationProvider(ABC):
    """Pluggable diarization provider contract.

    Implementations take an audio path and return a list of speaker
    segments. The mock provider (offline, no network) ships in PR-C; the
    real pyannote adapter is reserved for a follow-up once a HuggingFace
    token + real recording are available.
    """

    @abstractmethod
    def diarize(self, audio_path: str | Path, **options: Any) -> list[dict[str, Any]]:  # pragma: no cover - interface
        raise NotImplementedError


class MockDiarizationProvider(DiarizationProvider):
    """Stub until PR-C implementation lands."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = config_path

    def diarize(self, audio_path: str | Path, **options: Any) -> list[dict[str, Any]]:
        raise NotImplementedError("MockDiarizationProvider not implemented; PR-C in progress")


class PyannoteDiarizationProvider(DiarizationProvider):
    """Stub until PR-C implementation lands."""

    def diarize(self, audio_path: str | Path, **options: Any) -> list[dict[str, Any]]:
        raise NotImplementedError("PyannoteDiarizationProvider not implemented; PR-C in progress")


def normalize_speaker_segments(raw: list[Any]) -> list[dict[str, Any]]:
    """Stub until PR-C implementation lands."""
    raise NotImplementedError("normalize_speaker_segments not implemented; PR-C in progress")


def diarize_to_file(
    audio_path: str | Path,
    out_path: str | Path,
    *,
    provider: str = "mock",
    config_path: str | Path | None = None,
) -> Path:
    """Stub until PR-C implementation lands."""
    raise NotImplementedError("diarize_to_file not implemented; PR-C in progress")
