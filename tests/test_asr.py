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
