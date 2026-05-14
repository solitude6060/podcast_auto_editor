import json
from pathlib import Path

import podcast_auto_editor.cli as cli
from podcast_auto_editor.asr import ASRProviderError, StubTranscriptProvider, transcribe_to_file
from podcast_auto_editor.cli import main


def test_stub_provider_returns_valid_transcript_segments(tmp_path):
    provider = StubTranscriptProvider()

    payload = provider.transcribe(tmp_path / "episode.wav")

    assert payload["schema_version"] == "transcript.v1"
    assert payload["provider"] == "stub"
    assert payload["segments"] == [{"start": 0.0, "end": 1.0, "text": "Stub transcript for episode"}]


def test_transcribe_to_file_validates_and_writes_transcript(tmp_path):
    out = tmp_path / "transcript.json"

    path = transcribe_to_file(tmp_path / "episode.wav", out, provider_name="stub")

    assert path == out
    data = json.loads(out.read_text())
    assert data["schema_version"] == "transcript.v1"
    assert data["segments"][0]["text"] == "Stub transcript for episode"
    assert data["segments"][0]["start"] == 0.0


def test_transcribe_to_file_rejects_unknown_provider_without_writing(tmp_path):
    out = tmp_path / "transcript.json"

    try:
        transcribe_to_file(tmp_path / "episode.wav", out, provider_name="missing")
    except ASRProviderError as exc:
        assert "unknown transcript provider" in str(exc)
    else:
        raise AssertionError("expected provider error")

    assert not out.exists()


def test_transcribe_to_file_rejects_invalid_provider_output_without_writing(tmp_path, monkeypatch):
    class BadProvider:
        name = "bad"

        def transcribe(self, input_path, **options):
            return {"schema_version": "transcript.v1", "segments": [{"start": 1.0, "end": 0.5, "text": "bad"}]}

    monkeypatch.setattr("podcast_auto_editor.asr.PROVIDERS", {"bad": BadProvider})
    out = tmp_path / "transcript.json"

    try:
        transcribe_to_file(tmp_path / "episode.wav", out, provider_name="bad")
    except ASRProviderError as exc:
        assert "segment[0].end must be after start" in str(exc)
    else:
        raise AssertionError("expected validation error")

    assert not out.exists()


def test_transcribe_cli_writes_stub_transcript(tmp_path, capsys):
    out = tmp_path / "transcript.json"

    assert main(["transcribe", str(tmp_path / "episode.wav"), "--provider", "stub", "--out", str(out)]) == 0

    assert capsys.readouterr().out.strip() == str(out)
    assert json.loads(out.read_text())["segments"][0]["text"] == "Stub transcript for episode"


def test_transcribe_cli_reports_provider_errors(tmp_path, capsys):
    out = tmp_path / "transcript.json"

    assert main(["transcribe", str(tmp_path / "episode.wav"), "--provider", "missing", "--out", str(out)]) == 1

    assert "unknown transcript provider" in capsys.readouterr().err
    assert not out.exists()


def test_provider_names_include_optional_faster_whisper():
    from podcast_auto_editor.asr import provider_names

    assert "stub" in provider_names()
    assert "faster-whisper-local" in provider_names()


def test_faster_whisper_provider_missing_dependency_does_not_write(tmp_path, monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "faster_whisper":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    out = tmp_path / "transcript.json"

    try:
        transcribe_to_file(tmp_path / "episode.wav", out, provider_name="faster-whisper-local")
    except ASRProviderError as exc:
        assert "faster-whisper-local requires optional package faster-whisper" in str(exc)
    else:
        raise AssertionError("expected missing dependency error")

    assert not out.exists()


def test_faster_whisper_provider_normalizes_segments(tmp_path, monkeypatch):
    import sys
    import types

    calls = {}

    class Segment:
        start = 0.25
        end = 1.5
        text = " hello world "

    class WhisperModel:
        def __init__(self, model, device="auto", compute_type="auto"):
            calls["init"] = {"model": model, "device": device, "compute_type": compute_type}

        def transcribe(self, input_path, beam_size=5):
            calls["transcribe"] = {"input_path": str(input_path), "beam_size": beam_size}
            return [Segment()], object()

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=WhisperModel))

    transcript = cli.transcribe_to_file(
        tmp_path / "episode.wav",
        tmp_path / "transcript.json",
        provider_name="faster-whisper-local",
        model="large-v3",
        device="cuda",
        compute_type="float16",
    )

    data = json.loads(transcript.read_text())
    assert calls["init"] == {"model": "large-v3", "device": "cuda", "compute_type": "float16"}
    assert calls["transcribe"]["beam_size"] == 5
    assert data["provider"] == "faster-whisper-local"
    assert data["segments"] == [{"start": 0.25, "end": 1.5, "text": "hello world"}]


def test_transcribe_cli_passes_faster_whisper_options(tmp_path, monkeypatch):
    captured = {}

    def fake_transcribe_to_file(input_path, out_path, provider_name="stub", **options):
        captured["input_path"] = str(input_path)
        captured["out_path"] = str(out_path)
        captured["provider_name"] = provider_name
        captured["options"] = options
        Path(out_path).write_text(json.dumps({"schema_version": "transcript.v1", "segments": [{"start": 0.0, "end": 1.0, "text": "ok"}]}))
        return Path(out_path)

    monkeypatch.setattr(cli, "transcribe_to_file", fake_transcribe_to_file)
    out = tmp_path / "transcript.json"

    assert main([
        "transcribe",
        str(tmp_path / "episode.wav"),
        "--provider",
        "faster-whisper-local",
        "--model",
        "large-v3",
        "--device",
        "cuda",
        "--compute-type",
        "float16",
        "--out",
        str(out),
    ]) == 0

    assert captured["provider_name"] == "faster-whisper-local"
    assert captured["options"] == {"model": "large-v3", "device": "cuda", "compute_type": "float16"}
