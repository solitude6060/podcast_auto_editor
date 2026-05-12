import json
import tempfile
from pathlib import Path

from podcast_auto_editor.cli import main
from podcast_auto_editor.timeline import create_noop_timeline, write_json


def test_validate_cli_accepts_valid_timeline(capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 1.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "timeline.json"
        write_json(path, timeline)
        assert main(["validate", str(path)]) == 0
    assert "ok" in capsys.readouterr().out


def test_accept_cli_updates_operation_state():
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "op1", "type": "silence_cut", "source_range": {"start": 0.5, "end": 1.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 1, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None})
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "timeline.json"
        out = Path(td) / "accepted.json"
        write_json(src, timeline)
        assert main(["accept", str(src), "--out", str(out)]) == 0
        data = json.loads(out.read_text())
    assert data["operations"][0]["state"] == "accepted"
    assert data["operations"][0]["preview_ref"]


def test_render_cli_refuses_proposed_timeline_without_safe_flag(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "op1", "type": "retake_cut", "source_range": {"start": 0.5, "end": 1.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "low", "confidence": 0.95, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None})
    src = tmp_path / "timeline.json"
    write_json(src, timeline)
    assert main(["render", str(tmp_path / "missing.wav"), "--timeline", str(src), "--out", str(tmp_path / "runs")]) == 1
    assert "requires an accepted timeline" in capsys.readouterr().err
