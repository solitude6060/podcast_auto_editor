from pathlib import Path

import pytest

from podcast_auto_editor import fixtures
from podcast_auto_editor.cli import main
from podcast_auto_editor.media import MediaToolError


def test_make_demo_fixtures_creates_expected_files(monkeypatch, tmp_path):
    calls = []

    def fake_require_tool(name):
        assert name == "ffmpeg"
        return "/usr/bin/ffmpeg"

    def fake_run_command(command, text=True):
        calls.append(command)
        out = Path(command[-1])
        out.write_text("demo")

        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr(fixtures, "require_tool", fake_require_tool)
    monkeypatch.setattr(fixtures, "run_command", fake_run_command)

    paths = fixtures.make_demo_fixtures(tmp_path)
    assert paths["audio"].name == "demo-silence.wav"
    assert paths["video"].name == "demo-av.mp4"
    assert paths["audio"].exists()
    assert paths["video"].exists()
    assert len(calls) == 2


def test_demo_fixtures_cli_prints_paths(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(fixtures, "make_demo_fixtures", lambda out: {"audio": Path(out) / "a.wav", "video": Path(out) / "b.mp4"})
    assert main(["demo-fixtures", "--out", str(tmp_path / "demo")]) == 0
    out = capsys.readouterr().out
    assert "audio:" in out and "video:" in out


def test_make_demo_fixtures_propagates_ffmpeg_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(fixtures, "require_tool", lambda name: (_ for _ in ()).throw(MediaToolError("required tool not found on PATH: ffmpeg")))
    with pytest.raises(MediaToolError):
        fixtures.make_demo_fixtures(tmp_path)
