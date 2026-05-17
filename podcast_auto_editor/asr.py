from __future__ import annotations

import json
import subprocess
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


class WhisperCppLocalProvider:
    name = "whisper-cpp-local"

    def transcribe(self, input_path: str | Path, **options: Any) -> dict[str, Any]:
        binary = self._require_path(options, "binary", "--binary", "local whisper.cpp executable")
        model_path = self._require_path(options, "model_path", "--model-path", "local whisper.cpp model")
        output_prefix = Path(options.get("output_prefix") or Path(input_path).with_suffix(".whisper-cpp"))
        output_json = output_prefix.with_suffix(output_prefix.suffix + ".json") if output_prefix.suffix else Path(str(output_prefix) + ".json")
        language = str(options.get("language") or "auto")
        threads = options.get("threads")

        command = [str(binary), "-m", str(model_path), "-f", str(input_path), "-oj", "-of", str(output_prefix)]
        if language and language != "auto":
            command.extend(["-l", language])
        if threads is not None:
            command.extend(["-t", str(int(threads))])

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except OSError as exc:
            raise ASRProviderError(f"failed to execute whisper.cpp binary: {binary}") from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            suffix = f": {stderr}" if stderr else ""
            raise ASRProviderError(f"whisper.cpp transcription failed{suffix}") from exc

        try:
            data = json.loads(output_json.read_text())
        except FileNotFoundError as exc:
            raise ASRProviderError(f"whisper.cpp did not write expected JSON output: {output_json}") from exc
        except json.JSONDecodeError as exc:
            raise ASRProviderError(f"invalid whisper.cpp JSON output: {output_json}") from exc

        return {
            "schema_version": "transcript.v1",
            "provider": self.name,
            "source_media": str(input_path),
            "model_path": str(model_path),
            "segments": self._segments_from_whisper_cpp_json(data),
        }

    def _require_path(self, options: dict[str, Any], option_key: str, cli_flag: str, description: str) -> Path:
        raw_path = options.get(option_key)
        if not raw_path:
            raise ASRProviderError(f"{self.name} requires {cli_flag} pointing to a {description}")
        path = Path(raw_path)
        if not path.exists():
            raise ASRProviderError(f"{self.name} {cli_flag} does not exist: {path}")
        return path

    def _segments_from_whisper_cpp_json(self, data: Any) -> list[dict[str, Any]]:
        if not isinstance(data, dict):
            raise ASRProviderError("whisper.cpp JSON output must be an object")
        raw_segments = data.get("transcription") or data.get("segments")
        if not isinstance(raw_segments, list):
            raise ASRProviderError("whisper.cpp JSON output must contain transcription or segments array")

        segments: list[dict[str, Any]] = []
        for index, raw in enumerate(raw_segments):
            if not isinstance(raw, dict):
                raise ASRProviderError(f"whisper.cpp segment[{index}] must be an object")
            offsets = raw.get("offsets") if isinstance(raw.get("offsets"), dict) else {}
            if "from" in offsets and "to" in offsets:
                start = self._milliseconds_to_seconds(offsets["from"])
                end = self._milliseconds_to_seconds(offsets["to"])
            elif "start" in raw and "end" in raw:
                start = float(raw["start"])
                end = float(raw["end"])
            elif "t0" in raw and "t1" in raw:
                start = self._milliseconds_to_seconds(raw["t0"])
                end = self._milliseconds_to_seconds(raw["t1"])
            else:
                raise ASRProviderError(f"whisper.cpp segment[{index}] is missing timing fields")
            segments.append({"start": start, "end": end, "text": str(raw.get("text") or "").strip()})
        return segments

    def _milliseconds_to_seconds(self, value: Any) -> float:
        return float(value) / 1000.0


PROVIDERS: dict[str, type[TranscriptProvider]] = {
    StubTranscriptProvider.name: StubTranscriptProvider,
    FasterWhisperLocalProvider.name: FasterWhisperLocalProvider,
    WhisperCppLocalProvider.name: WhisperCppLocalProvider,
}


class Qwen3ASRLocalProvider:
    """Qwen3-ASR (Apache-2.0) — Chinese-optimised ASR with 20-min native chunks.

    Targets the upstream `qwen-asr` package API:
    ``Qwen3ASRModel.from_pretrained(model_id).transcribe(audio, language=...)``.
    Install via ``uv add qwen-asr`` (transformers) or ``uv add 'qwen-asr[vllm]'``
    (vLLM backend).

    Long audio (>20 min) must be chunked by the caller; the model card documents
    the 20-minute single-segment cap. Chunk-and-stitch helpers are out of scope.
    """

    name = "qwen3-asr-local"

    def transcribe(self, input_path: str | Path, **options: Any) -> dict[str, Any]:
        try:
            import qwen_asr  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ASRProviderError(
                "qwen3-asr-local requires the optional `qwen-asr` package; "
                "install with `uv add qwen-asr` (transformers backend) or "
                "`uv add 'qwen-asr[vllm]'` (vLLM backend). Single audio segment "
                "is capped at 20 minutes per the Qwen3-ASR model card; chunk "
                "long episodes before calling."
            ) from exc
        model_name = str(options.get("model") or "Qwen/Qwen3-ASR-1.7B")
        device = str(options.get("device") or "cuda")
        language = options.get("language")
        model_cls = getattr(qwen_asr, "Qwen3ASRModel", None)
        if model_cls is None:
            raise ASRProviderError(
                "installed `qwen_asr` package does not expose `Qwen3ASRModel`; "
                "the upstream API is `from qwen_asr import Qwen3ASRModel; "
                "Qwen3ASRModel.from_pretrained(model_id).transcribe(...)`. "
                "Upgrade qwen-asr or pin a version that exports the class."
            )
        try:
            model = model_cls.from_pretrained(model_name)
            kwargs: dict[str, Any] = {}
            if language:
                kwargs["language"] = str(language)
            raw_segments = model.transcribe(str(input_path), **kwargs)
        except ASRProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - surface every backend failure as ASRProviderError
            raise ASRProviderError(f"qwen-asr transcribe failed: {exc}") from exc
        if not isinstance(raw_segments, list):
            raise ASRProviderError(
                f"qwen-asr returned unexpected shape {type(raw_segments).__name__}; "
                "expected a list of {start, end, text} segments. If the upstream API "
                "changed, this provider needs adjustment (PR-X2.1)."
            )
        segments: list[dict[str, Any]] = []
        for seg in raw_segments:
            if not isinstance(seg, dict):
                continue
            text_value = str(seg.get("text") or "").strip()
            if not text_value:
                continue
            segments.append(
                {
                    "start": float(seg.get("start", 0.0)),
                    "end": float(seg.get("end", seg.get("start", 0.0))),
                    "text": text_value,
                }
            )
        return {
            "schema_version": "transcript.v1",
            "provider": self.name,
            "source_media": str(input_path),
            "model": model_name,
            "device": device,
            "segments": segments,
        }


PROVIDERS[Qwen3ASRLocalProvider.name] = Qwen3ASRLocalProvider


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
