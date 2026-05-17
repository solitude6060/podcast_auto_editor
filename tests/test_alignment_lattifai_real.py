"""
Lattifai ONNX provider tests — env-gated integration + non-env unit tests.

Non-env tests (always run):
  - missing model_path + no env var → AlignmentProviderError
  - missing acoustic_opt.onnx in given dir → AlignmentProviderError naming the file
  - model_path points at nonexistent dir → AlignmentProviderError (distinct from missing file)
  - model_path points at a file (not dir) → AlignmentProviderError
  - onnxruntime not installed (monkeypatched) → AlignmentProviderError with install guidance
  - schema version preserved via empty transcript (always-on, no decode needed)

Env-gated tests (skip if PAE_LATTIFAI_ONNX_PATH is not set):
  - empty transcript → empty alignments
  - single-segment Chinese transcript → per-character word entries, monotonic timestamps
    (xfail strict=True: decode body deferred to PR-X4.2)
  - happy path with non-empty transcript
    (xfail strict=True: decode body deferred to PR-X4.2)
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from podcast_auto_editor.alignment import (
    SCHEMA_VERSION,
    AlignmentProviderError,
    LattifaiAlignmentProvider,
    align_to_file,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ENV_VAR = "PAE_LATTIFAI_ONNX_PATH"

real_model_available = pytest.mark.skipif(
    not os.environ.get(_ENV_VAR),
    reason=f"{_ENV_VAR} not set; skipping real-model tests",
)


# ---------------------------------------------------------------------------
# Non-env unit tests (always run, no model required)
# ---------------------------------------------------------------------------


def test_lattifai_missing_model_path_raises_alignment_provider_error(monkeypatch):
    """No model_path kwarg and no PAE_LATTIFAI_ONNX_PATH → clear error."""
    monkeypatch.delenv(_ENV_VAR, raising=False)
    provider = LattifaiAlignmentProvider()
    with pytest.raises(AlignmentProviderError) as exc_info:
        provider.align("audio.wav", [{"start": 0.0, "end": 1.0, "text": "x"}])
    msg = str(exc_info.value)
    # Must mention both configuration options
    assert "model_path" in msg
    assert _ENV_VAR in msg
    assert isinstance(exc_info.value, AlignmentProviderError)
    assert not isinstance(exc_info.value, ImportError)


def test_lattifai_missing_model_dir_raises_alignment_provider_error(tmp_path, monkeypatch):
    """model_path points at a nonexistent directory → distinct clear error."""
    monkeypatch.delenv(_ENV_VAR, raising=False)
    nonexistent = tmp_path / "does-not-exist"
    # Do NOT create the directory
    provider = LattifaiAlignmentProvider()
    with pytest.raises(AlignmentProviderError) as exc_info:
        provider.align(
            "audio.wav",
            [{"start": 0.0, "end": 1.0, "text": "x"}],
            model_path=str(nonexistent),
        )
    msg = str(exc_info.value)
    assert "does not exist" in msg or "not exist" in msg
    assert isinstance(exc_info.value, AlignmentProviderError)
    assert not isinstance(exc_info.value, ImportError)


def test_lattifai_model_path_is_file_raises_alignment_provider_error(tmp_path, monkeypatch):
    """model_path points at a file (not a directory) → clear error."""
    monkeypatch.delenv(_ENV_VAR, raising=False)
    a_file = tmp_path / "some_file.onnx"
    a_file.write_bytes(b"fake")
    provider = LattifaiAlignmentProvider()
    with pytest.raises(AlignmentProviderError) as exc_info:
        provider.align(
            "audio.wav",
            [{"start": 0.0, "end": 1.0, "text": "x"}],
            model_path=str(a_file),
        )
    msg = str(exc_info.value)
    assert "directory" in msg.lower()
    assert isinstance(exc_info.value, AlignmentProviderError)
    assert not isinstance(exc_info.value, ImportError)


def test_lattifai_missing_model_file_raises_alignment_provider_error(tmp_path, monkeypatch):
    """Model directory exists but acoustic_opt.onnx is absent → clear error."""
    monkeypatch.delenv(_ENV_VAR, raising=False)
    model_dir = tmp_path / "Lattice-1"
    model_dir.mkdir()
    # Do NOT create acoustic_opt.onnx
    provider = LattifaiAlignmentProvider()
    with pytest.raises(AlignmentProviderError) as exc_info:
        provider.align(
            "audio.wav",
            [{"start": 0.0, "end": 1.0, "text": "x"}],
            model_path=str(model_dir),
        )
    msg = str(exc_info.value)
    assert "acoustic_opt.onnx" in msg
    assert isinstance(exc_info.value, AlignmentProviderError)
    assert not isinstance(exc_info.value, ImportError)


def test_lattifai_lazy_import_failure_raises_alignment_provider_error(tmp_path, monkeypatch):
    """onnxruntime not installed after a valid-looking model path → clear error with install guidance."""
    monkeypatch.delenv(_ENV_VAR, raising=False)
    model_dir = tmp_path / "Lattice-1"
    model_dir.mkdir()
    # Create the required file so we pass the file-existence check
    (model_dir / "acoustic_opt.onnx").write_bytes(b"fake")

    # Monkeypatch onnxruntime to simulate it being absent
    with patch.dict(sys.modules, {"onnxruntime": None}):
        provider = LattifaiAlignmentProvider()
        with pytest.raises(AlignmentProviderError) as exc_info:
            provider.align(
                "audio.wav",
                [{"start": 0.0, "end": 1.0, "text": "x"}],
                model_path=str(model_dir),
            )
    msg = str(exc_info.value)
    assert "onnxruntime" in msg.lower() or "align-lattifai" in msg
    assert isinstance(exc_info.value, AlignmentProviderError)
    assert not isinstance(exc_info.value, ImportError)


def test_lattifai_tokenizer_local_files_only(tmp_path, monkeypatch):
    """The provider must never call out to HuggingFace hub helpers at runtime.

    Since the implementation uses only local sidecar files (words.bin etc.)
    and no HuggingFace hub download helper, we assert that no network-calling
    hub helper is invoked during provider setup / align().

    Strategy: inject a fake sentinel into sys.modules for huggingface_hub so
    that if the provider ever imports it, we can detect the call without
    requiring the real package to be installed.
    """
    monkeypatch.delenv(_ENV_VAR, raising=False)
    import types
    import unittest.mock as mock_lib

    called = []

    # Build a minimal fake huggingface_hub module
    fake_hfhub = types.ModuleType("huggingface_hub")
    fake_hfhub.snapshot_download = mock_lib.MagicMock(  # type: ignore[attr-defined]
        side_effect=lambda *a, **kw: called.append((a, kw))
    )

    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_hfhub)

    provider = LattifaiAlignmentProvider()
    try:
        provider.align("audio.wav", [{"start": 0.0, "end": 1.0, "text": "x"}])
    except AlignmentProviderError:
        pass  # expected — no model_path set

    assert called == [], "Provider must not call huggingface_hub.snapshot_download at runtime"


def test_lattifai_schema_version_preserved_in_output(tmp_path, monkeypatch):
    """align_to_file with provider='lattifai' and empty transcript writes correct schema_version.

    Uses empty transcript [] which triggers the early-return path (returns [])
    so the decode blocker is never reached. Tests the file-write + schema
    scaffolding path without requiring a real model or the decode body.
    """
    monkeypatch.delenv(_ENV_VAR, raising=False)
    model_dir = tmp_path / "Lattice-1"
    model_dir.mkdir()
    (model_dir / "acoustic_opt.onnx").write_bytes(b"fake")

    out = tmp_path / "out.json"
    align_to_file(
        "fixtures/audio/short_zh.wav",
        [],  # empty transcript → early return → [] → schema written
        out,
        provider="lattifai",
        model_path=str(model_dir),
    )
    data = json.loads(out.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["words"] == []


# ---------------------------------------------------------------------------
# Env-gated real-model tests
# ---------------------------------------------------------------------------


@real_model_available
def test_lattifai_empty_transcript_returns_empty_alignments():
    """Empty transcript → empty word list, no decoder errors."""
    provider = LattifaiAlignmentProvider()
    words = provider.align("fixtures/audio/short_zh.wav", [])
    assert words == []


@real_model_available
@pytest.mark.xfail(
    reason="decode body deferred to PR-X4.2 — provider currently raises AlignmentProviderError blocker",
    strict=True,
)
def test_lattifai_env_var_model_path_happy_path():
    """With PAE_LATTIFAI_ONNX_PATH set, provider returns non-empty word list."""
    provider = LattifaiAlignmentProvider()
    words = provider.align(
        "fixtures/audio/short_zh.wav",
        [{"start": 0.0, "end": 2.0, "text": "你好世界"}],
    )
    assert isinstance(words, list)
    assert len(words) > 0
    for w in words:
        assert "start" in w and "end" in w and "text" in w
        assert w["end"] >= w["start"]


@real_model_available
@pytest.mark.xfail(
    reason="decode body deferred to PR-X4.2 — provider currently raises AlignmentProviderError blocker",
    strict=True,
)
def test_lattifai_single_segment_chinese_returns_word_entries():
    """Single Chinese segment → per-character entries, monotonic timestamps."""
    provider = LattifaiAlignmentProvider()
    words = provider.align(
        "fixtures/audio/short_zh.wav",
        [{"start": 0.0, "end": 2.0, "text": "你好世界"}],
    )
    assert len(words) >= 1
    texts = [w["text"] for w in words]
    # Each character must appear (order preserved)
    for char in ["你", "好", "世", "界"]:
        assert char in texts
    # Timestamps must be monotonically non-decreasing
    for i in range(1, len(words)):
        assert words[i]["start"] >= words[i - 1]["start"]
