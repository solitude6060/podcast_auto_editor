import builtins
import json
import os

import pytest

from podcast_auto_editor.alignment import (
    SCHEMA_VERSION,
    AlignmentProviderError,
    WhisperXAlignmentProvider,
    align_to_file,
)


def test_whisperx_empty_transcript_short_circuits_before_model_load(tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    words = WhisperXAlignmentProvider().align(
        "audio.wav",
        [],
        model_path=model_dir,
    )

    assert words == []


def test_whisperx_empty_transcript_writes_empty_artefact(tmp_path):
    out = tmp_path / "word_alignments.v1.json"

    result = align_to_file("audio.wav", [], out, provider="whisperx")

    assert result == out
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data == {
        "audio_path": "audio.wav",
        "schema_version": SCHEMA_VERSION,
        "words": [],
    }


def test_whisperx_missing_model_dir_raises_provider_error(tmp_path):
    missing_model = tmp_path / "missing-model"

    with pytest.raises(AlignmentProviderError, match="does not exist"):
        WhisperXAlignmentProvider().align(
            "audio.wav",
            [{"start": 0.0, "end": 1.0, "text": "你好"}],
            model_path=missing_model,
        )


def test_whisperx_missing_required_model_file_raises_provider_error(tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    with pytest.raises(AlignmentProviderError, match="missing"):
        WhisperXAlignmentProvider().align(
            "audio.wav",
            [{"start": 0.0, "end": 1.0, "text": "你好"}],
            model_path=model_dir,
        )


def test_whisperx_lazy_import_failure_raises_provider_error(tmp_path, monkeypatch):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "whisperx":
            raise ImportError("blocked whisperx import for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(AlignmentProviderError, match="whisperx"):
        WhisperXAlignmentProvider().align(
            "audio.wav",
            [{"start": 0.0, "end": 1.0, "text": "你好"}],
            model_path=model_dir,
        )


@pytest.mark.skipif(
    not os.environ.get("PAE_WHISPERX_ALIGN_MODEL"),
    reason="PAE_WHISPERX_ALIGN_MODEL is not set",
)
def test_whisperx_real_model_aligns_short_chinese_transcript():
    words = WhisperXAlignmentProvider().align(
        "tests/fixtures/short-zh.wav",
        [{"start": 0.0, "end": 1.0, "text": "你好"}],
    )

    assert words
    assert "".join(word["text"] for word in words).replace(" ", "") in {"你好", "你 好"}
    assert all(word["start"] <= word["end"] for word in words)
