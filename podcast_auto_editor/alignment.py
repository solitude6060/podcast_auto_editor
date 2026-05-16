from __future__ import annotations

import json
import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "word_alignments.v1"


class AlignmentError(Exception):
    """Raised when alignment input / output is invalid."""


class AlignmentProviderError(AlignmentError):
    """Raised when an alignment provider cannot run.

    Common reasons: required dependency (e.g. ``whisperx``) is not
    installed, an authentication token / model weights are missing, or a
    real-model integration has not yet been wired in.
    """


def _coerce_seconds(value: Any, field: str, idx: int) -> float:
    if value is None:
        raise AlignmentError(f"word[{idx}].{field} is required")
    if isinstance(value, bool):
        raise AlignmentError(f"word[{idx}].{field} must be numeric, not bool: {value!r}")
    try:
        seconds = float(value)
    except (TypeError, ValueError) as exc:
        raise AlignmentError(f"word[{idx}].{field} must be numeric: {value!r}") from exc
    if not math.isfinite(seconds):
        raise AlignmentError(f"word[{idx}].{field} must be a finite number: {value!r}")
    return seconds


def normalize_word_alignments(raw: list[Any]) -> list[dict[str, Any]]:
    """Validate + normalize word-level alignment items."""
    out: list[dict[str, Any]] = []
    for idx, raw_word in enumerate(raw):
        if not isinstance(raw_word, dict):
            raise AlignmentError(f"word[{idx}] must be an object")
        if "start" not in raw_word:
            raise AlignmentError(f"word[{idx}].start is required")
        if "end" not in raw_word:
            raise AlignmentError(f"word[{idx}].end is required")
        if "text" not in raw_word:
            raise AlignmentError(f"word[{idx}].text is required")
        start = _coerce_seconds(raw_word["start"], "start", idx)
        end = _coerce_seconds(raw_word["end"], "end", idx)
        if start < 0:
            raise AlignmentError(f"word[{idx}].start must be >= 0")
        if end < start:
            raise AlignmentError(f"word[{idx}].end must be >= start")
        text = str(raw_word["text"]).strip()
        if not text:
            raise AlignmentError(f"word[{idx}].text must not be empty")
        word = dict(raw_word)
        word["start"] = start
        word["end"] = end
        word["text"] = text
        out.append(word)
    return out


class AlignmentProvider(ABC):
    """Pluggable forced-alignment provider.

    Takes audio + sentence-level transcript and returns word-level (or
    character-level for CJK) alignments. The mock provider ships in
    PR-X3 for CI + dev-machine use; real WhisperX adapter requires
    optional ``whisperx`` install and Chinese phoneme weights.
    """

    @abstractmethod
    def align(
        self,
        audio_path: str | Path,
        transcript_segments: list[dict[str, Any]],
        **options: Any,
    ) -> list[dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError


class MockAlignmentProvider(AlignmentProvider):
    """Offline alignment provider that fakes word-level data from a config.

    Two modes:
    - ``config_path`` points at a JSON list of `{start, end, text}` to
      return verbatim (after validation). Used for golden / regression
      fixtures.
    - When ``config_path`` is None, the provider splits each transcript
      segment into evenly-spaced placeholder "words" (one per whitespace
      token; CJK text becomes one word per character). This exercises
      the schema end-to-end without requiring real alignment.
    """

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path: str | Path | None = config_path

    def align(
        self,
        audio_path: str | Path,  # noqa: ARG002
        transcript_segments: list[dict[str, Any]],
        **options: Any,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        if self.config_path is not None:
            data = json.loads(Path(self.config_path).read_text(encoding="utf-8"))
            if isinstance(data, dict):
                words = data.get("words", data.get("segments", []))
            elif isinstance(data, list):
                words = data
            else:
                raise AlignmentError("mock alignment config must be a JSON object or list")
            if not isinstance(words, list):
                raise AlignmentError("mock alignment config `words`/`segments` must be a list")
            return normalize_word_alignments(words)
        # Deterministic placeholder: split each segment evenly into tokens.
        words: list[dict[str, Any]] = []
        for seg in transcript_segments:
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start))
            text = str(seg.get("text", "")).strip()
            if not text or end <= start:
                continue
            tokens = text.split() if " " in text else list(text)
            if not tokens:
                continue
            span = (end - start) / len(tokens)
            for i, token in enumerate(tokens):
                words.append(
                    {
                        "start": start + i * span,
                        "end": start + (i + 1) * span,
                        "text": token,
                    }
                )
        return normalize_word_alignments(words)


class WhisperXAlignmentProvider(AlignmentProvider):
    """Lazy-import adapter for WhisperX forced alignment.

    Real model integration is deferred to PR-X3.1 (requires WhisperX
    install + a Chinese wav2vec2 phoneme model). This adapter raises a
    clear ``AlignmentProviderError`` distinguishing "dependency missing"
    from "integration deferred" so users know how to proceed.
    """

    def align(
        self,
        audio_path: str | Path,  # noqa: ARG002
        transcript_segments: list[dict[str, Any]],  # noqa: ARG002
        **options: Any,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        try:
            import whisperx  # noqa: F401
        except ImportError as exc:
            raise AlignmentProviderError(
                "whisperx is not installed; run `uv add whisperx` to enable real "
                "forced alignment. The community Chinese phoneme model "
                "`jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn` is the "
                "recommended weights for Chinese podcasts. Use `--provider mock` "
                "to ship without the heavy dependency."
            ) from exc
        raise AlignmentProviderError(
            "whisperx real-model integration is deferred to follow-up PR-X3.1; "
            "use `--provider mock` for now. PR-X3.1 will wire the Chinese phoneme "
            "model load + alignment call once a real recording is available for "
            "accuracy verification."
        )


def align_to_file(
    audio_path: str | Path,
    transcript_segments: list[dict[str, Any]],
    out_path: str | Path,
    *,
    provider: str = "mock",
    config_path: str | Path | None = None,
) -> Path:
    """Drive an alignment provider and write the canonical artefact."""
    if provider == "mock":
        prov: AlignmentProvider = MockAlignmentProvider(config_path=config_path)
    elif provider == "whisperx":
        prov = WhisperXAlignmentProvider()
    else:
        raise AlignmentError(f"unknown provider: {provider!r} (expected one of: mock, whisperx)")
    words = prov.align(audio_path, transcript_segments)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "audio_path": str(audio_path),
        "words": words,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return out
