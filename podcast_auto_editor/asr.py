from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from .timeline import write_json
from .transcript import TranscriptValidationError, normalize_transcript_segments


class ASRProviderError(ValueError):
    """Raised when transcript provider selection or output is unsafe."""


class TranscriptProvider(Protocol):
    name: str

    def transcribe(self, input_path: str | Path, **options: Any) -> dict[str, Any]:
        """Return a transcript.v1-compatible payload for input_path."""


class StubTranscriptProvider:
    name = "stub"

    def transcribe(self, input_path: str | Path, **options: Any) -> dict[str, Any]:
        stem = Path(input_path).stem or "episode"
        text = str(options.get("text") or f"Stub transcript for {stem}")
        return {
            "schema_version": "transcript.v1",
            "provider": self.name,
            "source_media": str(input_path),
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "text": text,
                }
            ],
        }


PROVIDERS: dict[str, type[TranscriptProvider]] = {
    StubTranscriptProvider.name: StubTranscriptProvider,
}


def provider_names() -> list[str]:
    return sorted(PROVIDERS)


def get_provider(name: str) -> TranscriptProvider:
    try:
        provider_type = PROVIDERS[name]
    except KeyError as exc:
        available = ", ".join(provider_names()) or "none"
        raise ASRProviderError(f"unknown transcript provider: {name}; available providers: {available}") from exc
    return provider_type()


def transcribe(input_path: str | Path, provider_name: str = "stub", **options: Any) -> dict[str, Any]:
    provider = get_provider(provider_name)
    payload = provider.transcribe(input_path, **options)
    try:
        segments = normalize_transcript_segments(payload)
    except TranscriptValidationError as exc:
        raise ASRProviderError(str(exc)) from exc
    return {
        "schema_version": "transcript.v1",
        "provider": provider_name,
        "source_media": str(input_path),
        "segments": segments,
    }


def transcribe_to_file(input_path: str | Path, out_path: str | Path, provider_name: str = "stub", **options: Any) -> Path:
    transcript = transcribe(input_path, provider_name=provider_name, **options)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, transcript)
    return out
