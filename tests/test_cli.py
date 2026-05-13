import json
import tempfile
from pathlib import Path

import podcast_auto_editor.cli as cli
from podcast_auto_editor.cli import main
from podcast_auto_editor.transcript import load_transcript_segments
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


def test_render_cli_refuses_plain_accepted_retake_without_review(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "retake1", "type": "retake_cut", "source_range": {"start": 0.5, "end": 1.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "accepted", "risk": "low", "confidence": 0.95, "provenance": {}, "preview_ref": "preview/before-after-preview.mp3", "diff_ref": "diff/timeline-diff.json", "recovery_ref": "recovery/recovery-map.json"})
    src = tmp_path / "timeline.json"
    write_json(src, timeline)

    assert main(["render", str(tmp_path / "missing.wav"), "--timeline", str(src), "--out", str(tmp_path / "runs")]) == 1
    assert "accepted retake_cut operations must carry successful auto_accept_policy or explicit manual review" in capsys.readouterr().err


def test_review_accept_cli_marks_selected_retake_as_manually_reviewed(tmp_path):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "retake1", "type": "retake_cut", "source_range": {"start": 0.5, "end": 1.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "low", "confidence": 0.95, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None})
    src = tmp_path / "timeline.json"
    out = tmp_path / "reviewed.json"
    write_json(src, timeline)

    assert main([
        "review-accept",
        str(src),
        "--operation-id",
        "retake1",
        "--reviewer",
        "producer",
        "--note",
        "Confirmed duplicate intro.",
        "--out",
        str(out),
    ]) == 0

    reviewed = json.loads(out.read_text())
    op = reviewed["operations"][0]
    assert op["state"] == "accepted"
    assert op["preview_ref"] and op["diff_ref"] and op["recovery_ref"]
    assert op["provenance"]["manual_review"]["reviewer"] == "producer"
    assert op["provenance"]["manual_review"]["decision"] == "accepted"
    assert op["provenance"]["manual_review"]["note"] == "Confirmed duplicate intro."
    assert reviewed["recovery"]["removed_segments"][0]["operation_id"] == "retake1"


def test_review_accept_cli_requires_explicit_operation_ids(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    src = tmp_path / "timeline.json"
    out = tmp_path / "reviewed.json"
    write_json(src, timeline)

    assert main(["review-accept", str(src), "--reviewer", "producer", "--out", str(out)]) == 1
    assert "requires at least one --operation-id" in capsys.readouterr().err


def test_undo_cli_requires_explicit_scope(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    src = tmp_path / "timeline.json"
    out = tmp_path / "restored.json"
    write_json(src, timeline)

    assert main(["undo", str(src), "--out", str(out)]) == 1
    assert "undo requires --all or at least one --operation-id" in capsys.readouterr().err


def test_undo_cli_restores_selected_accepted_operation(tmp_path):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 3.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "cut1", "type": "silence_cut", "source_range": {"start": 1.0, "end": 2.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "accepted", "risk": "deterministic", "confidence": 1.0, "provenance": {}, "preview_ref": "preview.mp3", "diff_ref": "diff.json", "recovery_ref": "recovery.json"})
    src = tmp_path / "timeline.json"
    out = tmp_path / "restored.json"
    write_json(src, timeline)

    assert main(["undo", str(src), "--operation-id", "cut1", "--reason", "restore intro pause", "--out", str(out)]) == 0
    restored = json.loads(out.read_text())
    assert restored["operations"][0]["state"] == "proposed"
    assert restored["operations"][0]["provenance"]["undo"]["reason"] == "restore intro pause"
    assert restored["recovery"]["removed_segments"] == []


def test_undo_cli_rejects_selected_non_accepted_operation(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 3.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "cut1", "type": "silence_cut", "source_range": {"start": 1.0, "end": 2.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 1.0, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None})
    src = tmp_path / "timeline.json"
    out = tmp_path / "restored.json"
    write_json(src, timeline)

    assert main(["undo", str(src), "--operation-id", "cut1", "--out", str(out)]) == 1
    assert "operation cut1 is not accepted" in capsys.readouterr().err


def test_load_transcript_segments_accepts_legacy_lists(tmp_path):
    transcript_json = tmp_path / "transcript.json"
    transcript_json.write_text(json.dumps([{"start": 0.0, "end": 0.5, "text": "hello"}]))
    assert load_transcript_segments(transcript_json) == [{"start": 0.0, "end": 0.5, "text": "hello"}]


def test_load_transcript_segments_accepts_versioned_wrapper(tmp_path):
    transcript_json = tmp_path / "transcript.json"
    transcript_json.write_text(json.dumps({"schema_version": "transcript.v1", "segments": [{"start": 0.0, "end": 0.5, "text": "hello"}]}))
    assert load_transcript_segments(transcript_json) == [{"start": 0.0, "end": 0.5, "text": "hello"}]


def test_transcript_import_validation_rejects_bad_shape(tmp_path, capsys, monkeypatch):
    input_path = tmp_path / "input.wav"
    input_path.write_bytes(b"stub")
    transcript_json = tmp_path / "transcript.json"
    transcript_json.write_text(json.dumps({"schema_version": "transcript.v1", "segments": [{"start": 0.0, "text": "missing end"}]}))

    def fake_run_pipeline(*args, **kwargs):
        raise AssertionError("run_pipeline should not be called for invalid transcript JSON")

    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)

    assert main(["run", str(input_path), "--out", str(tmp_path / "runs"), "--transcript-json", str(transcript_json)]) == 1
    assert "segment[0] missing required field(s): end" in capsys.readouterr().err


def test_dry_run_cli_writes_inspection_artifacts_without_media_exports(tmp_path, monkeypatch):
    def fake_probe(input_path, paths, config):
        timeline = create_noop_timeline({"path": str(input_path), "duration": 4.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
        write_json(paths.proposed_timeline, timeline)
        return timeline

    def fake_analyze(input_path, timeline, config):
        proposed = dict(timeline)
        proposed["operations"] = [{
            "operation_id": "cut1",
            "type": "silence_cut",
            "source_range": {"start": 1.0, "end": 2.0},
            "output_range": None,
            "affected_tracks": ["audio:0"],
            "state": "proposed",
            "risk": "deterministic",
            "confidence": 1.0,
            "provenance": {},
            "preview_ref": None,
            "diff_ref": None,
            "recovery_ref": None,
        }]
        return proposed

    monkeypatch.setattr(cli, "probe", fake_probe)
    monkeypatch.setattr(cli, "analyze", fake_analyze)
    monkeypatch.setattr(cli, "write_preview", lambda paths, input_path, timeline: paths.waveform.write_text(json.dumps({"type": "timeline-preview"})))

    assert main(["dry-run", str(tmp_path / "input.wav"), "--out", str(tmp_path / "runs"), "--episode-id", "ep1"]) == 0

    root = tmp_path / "runs" / "ep1"
    assert (root / "timeline.proposed.v1.json").exists()
    assert (root / "timeline.accepted.v1.json").exists()
    assert (root / "diff" / "timeline-diff.json").exists()
    assert (root / "recovery" / "recovery-map.json").exists()
    assert (root / "exports" / "transcript.json").exists()
    assert not (root / "exports" / "episode.edited.wav").exists()


def test_report_cli_outputs_json_and_markdown(tmp_path, capsys):
    root = tmp_path / "runs" / "ep1"
    (root / "diff").mkdir(parents=True)
    (root / "exports").mkdir()
    (root / "timeline.accepted.v1.json").write_text(json.dumps({"export_metadata": {"derived_assets": {"cue_errors": ["late cue"]}}}))
    (root / "diff" / "timeline-diff.json").write_text(json.dumps({"proposed_count": 2, "accepted_count": 1, "rejected_count": 1, "total_removed_duration": 1.5}))
    (root / "exports" / "transcript.json").write_text("{}")

    assert main(["report", str(root), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation_counts"]["accepted"] == 1
    assert payload["warnings"] == ["late cue"]

    assert main(["report", str(root), "--format", "markdown"]) == 0
    out = capsys.readouterr().out
    assert "# Podcast Auto Editor Report" in out
    assert "Accepted edits: 1" in out
