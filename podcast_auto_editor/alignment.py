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
    """Air-gapped ONNX adapter for LattifAI/Lattice-1 forced alignment.

    Implementation notes (PR-X4.1, 2026-05-18):
    -----------------------------------------------
    Model: https://huggingface.co/LattifAI/Lattice-1
    License: Apache-2.0
    Format: ONNX (acoustic_opt.onnx, ~129 MB)

    Verified ONNX interface (from lattifai-python source inspection):
      config.json: {"sample_rate": 16000, "frame_shift": 0.01, "subsampling_factor": 2}
      Input tensor : name="audios", dtype=float32, shape=(1, T) — raw PCM at 16 kHz
      Output tensor: dtype=float32, shape=(1, T_sub, vocab_size) — emission log-probs
                     where T_sub = T / subsampling_factor

    Decode blocker (documented 2026-05-18, see plan §2 follow-up):
      The upstream SDK (lattifai-python) decodes via k2py (k2 FST/lattice library).
      k2 has no PyPI wheel for Python >=3.11 (project requires 3.11+), so it cannot
      be listed as a dependency. Additionally, lattifai-python's tokenizer.tokenize()
      makes a POST to a backend service for pronunciation lookup + lattice construction
      — this violates the air-gap constraint.

      Until a local-only k2-free decode path is identified or contributed upstream,
      the ONNX inference body raises AlignmentProviderError with a clear blocker
      message rather than guessing at the algorithm (plan §2: "Do NOT guess at the
      algorithm — wrong decoder = wrong alignments = silent data corruption downstream").

    Setup: pre-download the model and set PAE_LATTIFAI_ONNX_PATH (see
      docs/runbooks/lattifai-onnx-setup.md) or pass model_path= to align().
    """

    def align(
        self,
        audio_path: str | Path,
        transcript_segments: list[dict[str, Any]],
        **options: Any,
    ) -> list[dict[str, Any]]:
        # ------------------------------------------------------------------
        # 1. Resolve model directory: explicit kwarg > env var
        # ------------------------------------------------------------------
        model_path: str | None = options.get("model_path") or os.environ.get(
            "PAE_LATTIFAI_ONNX_PATH"
        )
        if not model_path:
            raise AlignmentProviderError(
                "LattifaiAlignmentProvider requires a Lattice-1 model directory. "
                "Provide it via the model_path= keyword argument or by setting the "
                "PAE_LATTIFAI_ONNX_PATH environment variable to the path of the "
                "pre-downloaded LattifAI/Lattice-1 directory. "
                "See docs/runbooks/lattifai-onnx-setup.md for setup instructions."
            )

        # ------------------------------------------------------------------
        # 2. Validate model directory and required ONNX file exist
        # ------------------------------------------------------------------
        model_dir = Path(model_path)
        if not model_dir.exists():
            raise AlignmentProviderError(
                f"LattifaiAlignmentProvider: model directory does not exist: {model_dir}. "
                f"Set model_path= or PAE_LATTIFAI_ONNX_PATH to point at the directory "
                f"containing acoustic_opt.onnx. "
                f"See docs/runbooks/lattifai-onnx-setup.md."
            )
        if not model_dir.is_dir():
            raise AlignmentProviderError(
                f"LattifaiAlignmentProvider: model_path must be a directory, not a file: {model_dir}."
            )
        acoustic_file = model_dir / "acoustic_opt.onnx"
        if not acoustic_file.is_file():
            raise AlignmentProviderError(
                f"LattifaiAlignmentProvider: expected file acoustic_opt.onnx not found under "
                f"{model_dir}. Run the manual download per docs/runbooks/lattifai-onnx-setup.md."
            )

        # ------------------------------------------------------------------
        # 3. Early-return for empty transcript (no ONNX or decode work needed)
        # ------------------------------------------------------------------
        if not transcript_segments:
            return []

        # ------------------------------------------------------------------
        # 4. Lazy-import onnxruntime (optional dep group: align-lattifai)
        # ------------------------------------------------------------------
        try:
            import onnxruntime as ort  # noqa: F401
        except (ImportError, TypeError) as exc:
            raise AlignmentProviderError(
                "onnxruntime is not installed. Install the align-lattifai optional "
                "dependency group: uv sync --extra align-lattifai  "
                "(or: pip install .[align-lattifai]). "
                "For GPU inference install onnxruntime-gpu instead."
            ) from exc

        # ------------------------------------------------------------------
        # 5. ONNX inference + decode — BLOCKED pending local decode path
        #
        # What IS known (verified from upstream source, 2026-05-18):
        #   - Session: ort.InferenceSession(acoustic_opt.onnx, providers=[...])
        #   - Input:   session.run(None, {"audios": audio_float32_1xT})
        #   - Output:  emission log-probs (1, T_sub, vocab_size)
        #   - Decoder: k2.AlignSegments() with words.bin pronunciation dict
        #
        # What is BLOCKED:
        #   - k2 has no Python 3.11 PyPI wheel (project requires >=3.11)
        #   - lattifai-python tokenizer.tokenize() calls a backend HTTP endpoint
        #     (anti-air-gap); cannot be used here
        #   - No documented local-only decode path in the public SDK
        #
        # Action required: file a follow-up issue / PR to either:
        #   (a) use a pure-Python CTC greedy decode against words.bin if the
        #       ONNX output is CTC-compatible (unverified), or
        #   (b) wait for k2 to publish a Python 3.11 wheel, or
        #   (c) accept that this provider requires a separate Python 3.9/3.10
        #       subprocess for the k2 decode step.
        # ------------------------------------------------------------------
        raise AlignmentProviderError(
            "LattifaiAlignmentProvider: model file verified and onnxruntime "
            "available, but the forced-alignment decode step is blocked.\n\n"
            "Cause: Lattifai's decoder requires k2 (FST library) which has no "
            "Python 3.11 wheel on PyPI, and the SDK's tokenizer POSTs to a "
            "Lattifai backend (incompatible with the air-gap goal).\n\n"
            "Alternatives (see docs/plans/2026-05-18-pr-x4-1-lattifai-onnx-air-gap.md §9.5):\n"
            "  - Use --provider whisperx for the supported air-gap path "
            "(PR-X3.1: WhisperX + Chinese wav2vec2 phoneme model)\n"
            "  - Use --provider mock for offline placeholder alignments\n"
            "  - Track PR-X4.2 for the decode body (from-scratch viterbi over ONNX emissions)\n\n"
            "See docs/runbooks/lattifai-onnx-setup.md for current setup status."
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
    **provider_options: Any,
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
    words = prov.align(audio_path, transcript_segments, **provider_options)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "audio_path": str(audio_path),
        "words": words,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return out
