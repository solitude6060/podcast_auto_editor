import json
from pathlib import Path

import podcast_auto_editor.cli as cli
from podcast_auto_editor.cli import main
from podcast_auto_editor.timeline import create_noop_timeline, write_json


def _patch_dry_run_primitives(monkeypatch):
    def fake_probe(input_path, paths, config):
        timeline = create_noop_timeline({"path": str(input_path), "duration": 6.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
        write_json(paths.proposed_timeline, timeline)
        return timeline

    def fake_analyze(input_path, timeline, config):
        proposed = dict(timeline)
        proposed["operations"] = [{
            "operation_id": f"cut-{Path(input_path).stem}",
            "type": "silence_cut",
            "source_range": {"start": 1.0, "end": 2.25},
            "output_range": None,
            "affected_tracks": ["audio:0"],
            "state": "proposed",
            "risk": "deterministic",
            "confidence": 1.0,
            "provenance": {"detector": "test"},
            "preview_ref": None,
            "diff_ref": None,
            "recovery_ref": None,
        }]
        return proposed

    monkeypatch.setattr(cli, "probe", fake_probe)
    monkeypatch.setattr(cli, "analyze", fake_analyze)
    monkeypatch.setattr(cli, "write_preview", lambda paths, input_path, timeline: paths.waveform.write_text(json.dumps({"type": "timeline-preview"})))


def test_project_init_cli_writes_local_manifest(tmp_path, capsys):
    project_dir = tmp_path / "show-project"

    assert main(["project", "init", str(project_dir), "--name", "My Show"]) == 0

    manifest_path = project_dir / "podcast-project.v1.json"
    assert capsys.readouterr().out.strip() == str(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    assert manifest["schema_version"] == "podcast-project.v1"
    assert manifest["name"] == "My Show"
    assert manifest["episodes"] == []


def test_batch_dry_run_writes_json_and_markdown_reports(tmp_path, monkeypatch, capsys):
    _patch_dry_run_primitives(monkeypatch)

    assert main(["batch", "dry-run", str(tmp_path / "ep1.wav"), str(tmp_path / "ep2.wav"), "--out", str(tmp_path / "runs")]) == 0

    batch_dir = tmp_path / "runs" / "batch"
    report_json = batch_dir / "batch-report.json"
    report_md = batch_dir / "batch-report.md"
    assert capsys.readouterr().out.strip() == str(report_json)
    report = json.loads(report_json.read_text())
    assert report["summary"] == {"total": 2, "succeeded": 2, "failed": 0}
    assert report["total_removed_duration"] == 2.5
    assert [episode["status"] for episode in report["episodes"]] == ["succeeded", "succeeded"]
    assert report_md.exists()
    assert "# Batch Dry-run Report" in report_md.read_text()
    assert not (tmp_path / "runs" / "ep1" / "exports" / "episode.edited.wav").exists()


def test_batch_dry_run_records_failures_and_continues(tmp_path, monkeypatch):
    _patch_dry_run_primitives(monkeypatch)
    real_probe = cli.probe

    def sometimes_failing_probe(input_path, paths, config):
        if Path(input_path).name == "bad.wav":
            raise ValueError("bad media")
        return real_probe(input_path, paths, config)

    monkeypatch.setattr(cli, "probe", sometimes_failing_probe)

    assert main(["batch", "dry-run", str(tmp_path / "bad.wav"), str(tmp_path / "good.wav"), "--out", str(tmp_path / "runs")]) == 1

    report = json.loads((tmp_path / "runs" / "batch" / "batch-report.json").read_text())
    assert report["summary"] == {"total": 2, "succeeded": 1, "failed": 1}
    assert report["episodes"][0]["status"] == "failed"
    assert report["episodes"][0]["error"] == "bad media"
    assert report["episodes"][1]["status"] == "succeeded"


def test_batch_report_markdown_escapes_table_cells(tmp_path, monkeypatch):
    _patch_dry_run_primitives(monkeypatch)
    monkeypatch.setattr(cli, "probe", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("bad | media")))

    assert main(["batch", "dry-run", str(tmp_path / "bad.wav"), "--out", str(tmp_path / "runs")]) == 1

    report_markdown = (tmp_path / "runs" / "batch" / "batch-report.md").read_text()
    assert "bad \\| media" in report_markdown


def test_batch_dry_run_fail_fast_stops_after_first_failure(tmp_path, monkeypatch):
    _patch_dry_run_primitives(monkeypatch)
    monkeypatch.setattr(cli, "probe", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("bad media")))

    assert main(["batch", "dry-run", str(tmp_path / "bad.wav"), str(tmp_path / "skipped.wav"), "--out", str(tmp_path / "runs"), "--fail-fast"]) == 1

    report = json.loads((tmp_path / "runs" / "batch" / "batch-report.json").read_text())
    assert report["summary"] == {"total": 1, "succeeded": 0, "failed": 1}
    assert len(report["episodes"]) == 1
