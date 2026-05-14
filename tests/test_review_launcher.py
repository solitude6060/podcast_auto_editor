from pathlib import Path

import pytest

from podcast_auto_editor.cli import main
from podcast_auto_editor.local_review_server import build_launcher_script, build_linux_desktop_entry, write_review_launcher


def test_build_launcher_script_quotes_paths_and_uses_localhost():
    script = build_launcher_script('/tmp/show one/run;bad', host='127.0.0.1', port=8765)

    assert script.startswith('#!/usr/bin/env sh')
    assert "review serve" in script
    assert "--host 127.0.0.1" in script
    assert "--port 8765" in script
    assert "'/tmp/show one/run;bad'" in script


def test_write_review_launcher_writes_executable_script_and_desktop_file(tmp_path):
    script_path = tmp_path / "Launch Review UI.sh"
    desktop_path = tmp_path / "Review UI.desktop"

    result = write_review_launcher(tmp_path / "run dir", script_path, desktop_out=desktop_path, host="localhost", port=9000)

    assert result == {"script": script_path, "desktop": desktop_path}
    assert script_path.exists()
    assert script_path.stat().st_mode & 0o111
    script = script_path.read_text()
    assert "--host localhost" in script
    assert "--port 9000" in script
    desktop = desktop_path.read_text()
    assert "Type=Application" in desktop
    assert f"Exec={script_path}" in desktop
    assert "Terminal=false" in desktop


def test_build_linux_desktop_entry_escapes_newlines():
    entry = build_linux_desktop_entry(Path("/tmp/launcher"), name="Review\nUI")

    assert "Name=Review UI" in entry
    assert "\nUI" not in entry


def test_write_review_launcher_rejects_non_local_host_before_writing(tmp_path):
    script_path = tmp_path / "review.sh"

    with pytest.raises(ValueError, match="review server binds to localhost only"):
        write_review_launcher(tmp_path / "run", script_path, host="0.0.0.0")

    assert not script_path.exists()


def test_review_launcher_cli_writes_files(tmp_path, capsys):
    script_path = tmp_path / "review.sh"
    desktop_path = tmp_path / "review.desktop"

    assert main(["review", "launcher", str(tmp_path / "run"), "--out", str(script_path), "--desktop-out", str(desktop_path)]) == 0

    assert capsys.readouterr().out.strip() == str(script_path)
    assert script_path.exists()
    assert desktop_path.exists()


def test_review_launcher_cli_rejects_non_local_host(tmp_path, capsys):
    script_path = tmp_path / "review.sh"

    assert main(["review", "launcher", str(tmp_path / "run"), "--out", str(script_path), "--host", "0.0.0.0"]) == 1

    assert "review server binds to localhost only" in capsys.readouterr().err
    assert not script_path.exists()
