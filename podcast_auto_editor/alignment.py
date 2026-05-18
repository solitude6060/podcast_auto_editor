from __future__ import annotations

import json
import math
import os
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
        # Tokenization rule (triple-review fix): split on ANY whitespace first
        # (`text.split()` handles \n, \t, multiple spaces, etc.). Each resulting
        # token that is pure ASCII stays as one token; non-ASCII tokens (CJK)
        # split into individual characters. So:
        #   "hello world"   -> ["hello", "world"]
        #   "hello\nworld"  -> ["hello", "world"]  (newline-only no longer falls through to char-split)
        #   "你好世界"        -> ["你", "好", "世", "界"]
        #   "hello 世界"     -> ["hello", "世", "界"]  (was ["hello", "世界"] pre-fix)
        words: list[dict[str, Any]] = []
        for seg in transcript_segments:
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start))
            text = str(seg.get("text", "")).strip()
            if not text or end <= start:
                continue
            tokens: list[str] = []
            whitespace_split = text.split()
            for piece in whitespace_split:
                if piece.isascii():
                    tokens.append(piece)
                else:
                    tokens.extend(list(piece))
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


class LattifaiAlignmentProvider(AlignmentProvider):
    """Lazy-import adapter for Lattifai Lattice-1 forced alignment.

    Per `docs/research/2026-05-17-chinese-asr-models.md`:
    - Lattice-1 model itself is Apache-2.0, ONNX, runs entirely on the
      local machine (onnxruntime + CUDA/MPS/CoreML providers).
    - Audio never leaves the box during alignment.
    - **But** the official `lattifai-python` SDK by default constructs a
      `SyncAPIClient` that phones home for quota / usage tracking even
      though the model is local. For strict "nothing leaves my box"
      operation, callers must either accept the telemetry caveat
      (auth via `lai auth trial` for free 120-min credit) or bypass the
      SDK and load https://huggingface.co/LattifAI/Lattice-1 directly
      via onnxruntime (unofficial; tokenizer/decoder hookup is the
      caller's responsibility — out of scope for PR-X4).

    Real model integration is deferred to PR-X4.1.
    """

    def align(
        self,
        audio_path: str | Path,  # noqa: ARG002
        transcript_segments: list[dict[str, Any]],  # noqa: ARG002
        **options: Any,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        try:
            import lattifai  # noqa: F401
        except ImportError as exc:
            raise AlignmentProviderError(
                "lattifai is not installed; run `uv add lattifai` to enable Lattifai "
                "Lattice-1 alignment. Note: the official SDK initialises an API client "
                "that may require authentication / usage tracking even though the ONNX "
                "model itself runs locally. Use `--provider whisperx` for a fully "
                "air-gapped path, or load LattifAI/Lattice-1 ONNX directly via "
                "onnxruntime if you need to bypass the SDK. See "
                "docs/research/2026-05-17-chinese-asr-models.md §2.2 for the "
                "telemetry-vs-air-gap trade-off."
            ) from exc
        raise AlignmentProviderError(
            "lattifai real-model integration is deferred to follow-up PR-X4.1; "
            "use `--provider mock` or `--provider whisperx` for now. PR-X4.1 will "
            "wire the LattifaiClient + auth handling once the air-gap-vs-telemetry "
            "trade-off has been explicitly decided."
        )


class WhisperXAlignmentProvider(AlignmentProvider):
    """Lazy-import adapter for WhisperX forced alignment.

    Real model integration is deferred to PR-X3.1 (requires WhisperX
    install + a Chinese wav2vec2 phoneme model). This adapter raises a
    clear ``AlignmentProviderError`` distinguishing "dependency missing"
    from "integration deferred" so users know how to proceed.
    """

    def align(
        self,
        audio_path: str | Path,
        transcript_segments: list[dict[str, Any]],
        **options: Any,
    ) -> list[dict[str, Any]]:
        model_path_option = options.get("model_path") or os.environ.get("PAE_WHISPERX_ALIGN_MODEL")
        if not transcript_segments:
            return []
        if not model_path_option:
            raise AlignmentProviderError(
                "model_path is required; pass model_path=... or set PAE_WHISPERX_ALIGN_MODEL"
            )
        model_path = Path(model_path_option)
        if not model_path.exists():
            raise AlignmentProviderError(f"model path does not exist: {model_path}")
        if not model_path.is_dir():
            raise AlignmentProviderError(f"model path is not a directory: {model_path}")
        if not (model_path / "config.json").exists():
            raise AlignmentProviderError(f"model missing required file config.json: {model_path}")
        try:
            import torch
            import whisperx
        except ImportError as exc:
            raise AlignmentProviderError(f"whisperx is not installed: {exc}") from exc
        device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            model, metadata = whisperx.load_align_model(
                language_code="zh",
                model_name=str(model_path),
                device=device,
            )
            result = whisperx.align(transcript_segments, model, metadata, audio_path, device)
        except Exception as exc:
            raise AlignmentProviderError(f"whisperx alignment failed: {exc}") from exc
        words: list[dict[str, Any]] = []
        for segment in result["segments"]:
            for word in segment.get("words", []):
                if word.get("start") is None or word.get("end") is None:
                    continue
                words.append(
                    {
                        "start": word["start"],
                        "end": word["end"],
                        "text": word["word"],
                    }
                )
        return normalize_word_alignments(words)


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
    elif provider == "lattifai":
        prov = LattifaiAlignmentProvider()
    else:
        raise AlignmentError(f"unknown provider: {provider!r} (expected one of: mock, whisperx, lattifai)")
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
