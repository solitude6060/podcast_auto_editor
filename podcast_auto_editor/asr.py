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


class FasterWhisperLocalProvider:
    name = "faster-whisper-local"

    def transcribe(self, input_path: str | Path, **options: Any) -> dict[str, Any]:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ASRProviderError(
                "faster-whisper-local requires optional package faster-whisper; "
                "install it in your local RTX 4090 environment before selecting this provider"
            ) from exc
        model_name = str(options.get("model") or "large-v3")
        device = str(options.get("device") or "cuda")
        compute_type = str(options.get("compute_type") or "float16")
        beam_size = int(options.get("beam_size") or 5)
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        segments, _info = model.transcribe(str(input_path), beam_size=beam_size)
        return {
            "schema_version": "transcript.v1",
            "provider": self.name,
            "source_media": str(input_path),
            "model": model_name,
            "device": device,
            "compute_type": compute_type,
            "segments": [
                {
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": str(segment.text).strip(),
                }
                for segment in segments
            ],
        }


PROVIDERS: dict[str, type[TranscriptProvider]] = {
    StubTranscriptProvider.name: StubTranscriptProvider,
    FasterWhisperLocalProvider.name: FasterWhisperLocalProvider,
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
