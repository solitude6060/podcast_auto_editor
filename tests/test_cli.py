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


def test_review_accept_cli_can_manually_accept_speech_cut(tmp_path):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "speech1", "type": "speech_cut", "source_range": {"start": 0.5, "end": 0.8}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "medium", "confidence": 0.8, "provenance": {"reason": "filler"}, "preview_ref": None, "diff_ref": None, "recovery_ref": None})
    src = tmp_path / "timeline.json"
    out = tmp_path / "reviewed.json"
    write_json(src, timeline)

    assert main(["review-accept", str(src), "--operation-id", "speech1", "--reviewer", "producer", "--out", str(out)]) == 0
    reviewed = json.loads(out.read_text())
    assert reviewed["operations"][0]["state"] == "accepted"
    assert reviewed["operations"][0]["provenance"]["manual_review"]["decision"] == "accepted"


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
    (root / "timeline.accepted.v1.json").write_text(json.dumps({
        "operations": [{
            "operation_id": "speech1",
            "type": "speech_cut",
            "source_range": {"start": 0.5, "end": 0.75},
            "output_range": None,
            "affected_tracks": ["audio:0"],
            "state": "proposed",
            "risk": "medium",
            "confidence": 0.81,
            "provenance": {"detector": "transcript.speech_cleanup_heuristic"},
            "preview_ref": "preview/speech1.mp3",
            "diff_ref": None,
            "recovery_ref": None,
        }],
        "export_metadata": {"derived_assets": {"cue_errors": ["late cue"]}},
    }))
    (root / "diff" / "timeline-diff.json").write_text(json.dumps({"proposed_count": 2, "accepted_count": 1, "rejected_count": 1, "total_removed_duration": 1.5}))
    (root / "exports" / "transcript.json").write_text("{}")

    assert main(["report", str(root), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation_counts"]["accepted"] == 1
    assert payload["warnings"] == ["late cue"]
    assert payload["operation_groups"]["by_risk"] == {"medium": 1}
    assert payload["operation_groups"]["by_detector"] == {"transcript.speech_cleanup_heuristic": 1}

    assert main(["report", str(root), "--format", "markdown"]) == 0
    out = capsys.readouterr().out
    assert "# Podcast Auto Editor Report" in out
    assert "Accepted edits: 1" in out
    assert "medium: 1" in out
    assert "transcript.speech_cleanup_heuristic: 1" in out


def test_review_list_cli_outputs_operation_preview_table(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 4.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({
        "operation_id": "cut1",
        "type": "silence_cut",
        "source_range": {"start": 1.0, "end": 2.5},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "proposed",
        "risk": "deterministic",
        "confidence": 1.0,
        "provenance": {
            "operation_preview": {
                "before_after_ref": "preview/operations/cut1/before-after.mp3",
                "removed_ref": "preview/operations/cut1/removed.mp3",
            }
        },
        "preview_ref": "preview/operations/cut1/before-after.mp3",
        "diff_ref": None,
        "recovery_ref": None,
    })
    src = tmp_path / "timeline.json"
    write_json(src, timeline)

    assert main(["review-list", str(src)]) == 0

    out = capsys.readouterr().out
    assert "| Operation | Type | State | Risk | Confidence | Source | Preview | Removed |" in out
    assert "| cut1 | silence_cut | proposed | deterministic | 1.000 | 1.000-2.500 | preview/operations/cut1/before-after.mp3 | preview/operations/cut1/removed.mp3 |" in out


def test_review_list_cli_outputs_machine_readable_rows(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 4.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({
        "operation_id": "speech1",
        "type": "speech_cut",
        "source_range": {"start": 0.25, "end": 0.75},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "accepted",
        "risk": "medium",
        "confidence": 0.83,
        "provenance": {},
        "preview_ref": "preview/legacy.mp3",
        "diff_ref": "diff/timeline-diff.json",
        "recovery_ref": "recovery/recovery-map.json",
    })
    src = tmp_path / "timeline.json"
    write_json(src, timeline)

    assert main(["review-list", str(src), "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "timeline": str(src),
        "operation_count": 1,
        "operations": [{
            "operation_id": "speech1",
            "type": "speech_cut",
            "state": "accepted",
            "risk": "medium",
            "confidence": 0.83,
            "source": {"start": 0.25, "end": 0.75},
            "preview_ref": "preview/legacy.mp3",
            "removed_ref": None,
        }],
    }


def test_explain_cli_outputs_json_for_operation(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 4.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({
        "operation_id": "speech1",
        "type": "speech_cut",
        "source_range": {"start": 0.5, "end": 0.75},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "proposed",
        "risk": "medium",
        "confidence": 0.81,
        "provenance": {"detector": "transcript.speech_cleanup_heuristic", "reason": "filler_phrase", "evidence_text": "um"},
        "preview_ref": "preview/speech1.mp3",
        "diff_ref": None,
        "recovery_ref": None,
    })
    src = tmp_path / "timeline.json"
    write_json(src, timeline)

    assert main(["explain", str(src), "--operation-id", "speech1", "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["operation_id"] == "speech1"
    assert payload["detector"] == "transcript.speech_cleanup_heuristic"
    assert payload["required_review"] == "manual_review_required"
    assert "ai_explanation" not in payload


def test_explain_cli_reports_missing_operation(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 1.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    src = tmp_path / "timeline.json"
    write_json(src, timeline)

    assert main(["explain", str(src), "--operation-id", "missing"]) == 1
    assert "operation missing was not found" in capsys.readouterr().err


def test_explain_cli_with_ai_dry_prompt_outputs_ai_fields(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 4.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({
        "operation_id": "speech1",
        "type": "speech_cut",
        "source_range": {"start": 0.5, "end": 0.75},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "proposed",
        "risk": "medium",
        "confidence": 0.81,
        "provenance": {"detector": "transcript.speech_cleanup_heuristic", "reason": "filler_phrase", "evidence_text": "um"},
        "preview_ref": "preview/speech1.mp3",
        "diff_ref": None,
        "recovery_ref": None,
    })
    src = tmp_path / "timeline.json"
    write_json(src, timeline)
    transcript_json = tmp_path / "transcript.json"
    transcript_json.write_text(json.dumps([{"start": 0.0, "end": 0.4, "text": "hello"}]))

    assert main([
        "explain",
        str(src),
        "--operation-id",
        "speech1",
        "--with-ai",
        "--dry-prompt",
        "--transcript-json",
        str(transcript_json),
        "--format",
        "json",
    ]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["operation_id"] == "speech1"
    assert payload["ai_explanation"]["dry_prompt"] is True


def test_ai_draft_cli_requires_transcript_json(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 4.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({
        "operation_id": "speech1",
        "type": "speech_cut",
        "source_range": {"start": 0.5, "end": 0.75},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "proposed",
        "risk": "medium",
        "confidence": 0.81,
        "provenance": {"detector": "transcript.speech_cleanup_heuristic", "reason": "filler_phrase"},
        "preview_ref": "preview/speech1.mp3",
        "diff_ref": None,
        "recovery_ref": None,
    })
    src = tmp_path / "timeline.json"
    write_json(src, timeline)

    assert main(["ai", "draft", "--timeline", str(src)]) == 1
    assert "ai draft requires --transcript-json" in capsys.readouterr().err


def test_ai_draft_cli_dry_prompt_writes_payload_json_and_file(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 4.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({
        "operation_id": "speech1",
        "type": "speech_cut",
        "state": "proposed",
        "source_range": {"start": 0.5, "end": 0.75},
    })
    timeline["operations"].append({
        "operation_id": "retake1",
        "type": "retake_cut",
        "state": "proposed",
        "source_range": {"start": 2.0, "end": 2.8},
    })
    timeline["operations"].append({
        "operation_id": "silence1",
        "type": "silence_cut",
        "state": "proposed",
        "source_range": {"start": 3.0, "end": 3.4},
    })
    timeline_path = tmp_path / "timeline.json"
    write_json(timeline_path, timeline)
    transcript_json = tmp_path / "transcript.json"
    transcript_json.write_text(json.dumps([{"start": 0.0, "end": 0.4, "text": "hello there"}]))

    assert main([
        "ai",
        "draft",
        "--timeline",
        str(timeline_path),
        "--transcript-json",
        str(transcript_json),
        "--dry-prompt",
        "--format",
        "json",
    ]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_prompt"] is True
    assert payload["schema_version"] == "ai-draft.v1"
    assert payload["metadata"]["candidate_operation_count"] == 2
    expected_path = timeline_path.parent / "ai" / "ai-draft.v1.json"
    assert expected_path.exists()
    assert json.loads(expected_path.read_text()) == payload


def test_ai_draft_cli_dry_run_alias_uses_dry_prompt_behavior(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 4.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({
        "operation_id": "speech1",
        "type": "speech_cut",
        "state": "proposed",
        "source_range": {"start": 0.5, "end": 0.75},
    })
    timeline_path = tmp_path / "timeline.json"
    write_json(timeline_path, timeline)
    transcript_json = tmp_path / "transcript.json"
    transcript_json.write_text(json.dumps([{"start": 0.0, "end": 0.4, "text": "hello there"}]))

    assert main([
        "ai",
        "draft",
        "--timeline",
        str(timeline_path),
        "--transcript-json",
        str(transcript_json),
        "--dry-run",
        "--format",
        "json",
    ]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_prompt"] is True
    assert payload["metadata"]["candidate_operation_count"] == 1


def test_run_cli_passes_export_profile_overrides(tmp_path, monkeypatch, capsys):
    captured = {}

    def fake_run_pipeline(input_path, output_dir, config, episode_id=None, transcript_segments=None, export_profile_names=None):
        captured["export_profile_names"] = export_profile_names
        root = tmp_path / "runs" / "ep1"
        root.mkdir(parents=True)
        return type("Paths", (), {"root": root})()

    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)

    assert main([
        "run",
        str(tmp_path / "input.wav"),
        "--out",
        str(tmp_path / "runs"),
        "--episode-id",
        "ep1",
        "--export-profile",
        "podcast-mono",
        "--export-profile",
        "archive-wav",
    ]) == 0

    assert captured["export_profile_names"] == ["podcast-mono", "archive-wav"]
    assert str(tmp_path / "runs" / "ep1") in capsys.readouterr().out


def test_render_cli_reports_unknown_export_profile(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 1.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    src = tmp_path / "timeline.json"
    write_json(src, timeline)

    assert main([
        "render",
        str(tmp_path / "input.wav"),
        "--timeline",
        str(src),
        "--out",
        str(tmp_path / "runs"),
        "--export-profile",
        "video-social",
    ]) == 1

    assert "unknown export profile: video-social" in capsys.readouterr().err


def test_review_status_cli_outputs_session_summary(tmp_path, capsys):
    session = {
        "schema_version": "review-session.v1",
        "source_timeline": "timeline.json",
        "decisions": [
            {"operation_id": "speech1", "decision": "accept", "reviewer": "producer", "note": "ok", "decided_at": "2026-05-13T00:00:00Z"}
        ],
    }
    path = tmp_path / "review-session.json"
    path.write_text(json.dumps(session))

    assert main(["review", "status", str(path)]) == 0

    out = capsys.readouterr().out
    assert "# Review Session Status" in out
    assert "Accepted: 1" in out


def test_review_status_cli_outputs_json(tmp_path, capsys):
    session = {"schema_version": "review-session.v1", "source_timeline": "timeline.json", "decisions": []}
    path = tmp_path / "review-session.json"
    path.write_text(json.dumps(session))

    assert main(["review", "status", str(path), "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "review-session.v1"
    assert payload["decision_counts"]["accepted"] == 0


def test_review_decide_cli_appends_decision(tmp_path):
    session = {"schema_version": "review-session.v1", "source_timeline": "timeline.json", "decisions": []}
    path = tmp_path / "review-session.json"
    path.write_text(json.dumps(session))

    assert main([
        "review",
        "decide",
        str(path),
        "--operation-id",
        "speech1",
        "--decision",
        "accept",
        "--reviewer",
        "producer",
        "--note",
        "confirmed",
        "--decided-at",
        "2026-05-13T00:00:00Z",
    ]) == 0

    updated = json.loads(path.read_text())
    assert updated["decisions"] == [{
        "operation_id": "speech1",
        "decision": "accept",
        "reviewer": "producer",
        "note": "confirmed",
        "decided_at": "2026-05-13T00:00:00Z",
    }]


def test_review_rebuild_cli_replays_session_to_timeline(tmp_path):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({
        "operation_id": "speech1",
        "type": "speech_cut",
        "source_range": {"start": 0.5, "end": 0.75},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "proposed",
        "risk": "medium",
        "confidence": 0.8,
        "provenance": {},
        "preview_ref": "preview/speech1.mp3",
        "diff_ref": None,
        "recovery_ref": None,
    })
    timeline_path = tmp_path / "timeline.proposed.v1.json"
    session_path = tmp_path / "review-session.json"
    out = tmp_path / "timeline.accepted.v1.json"
    write_json(timeline_path, timeline)
    session_path.write_text(json.dumps({
        "schema_version": "review-session.v1",
        "source_timeline": str(timeline_path),
        "decisions": [{"operation_id": "speech1", "decision": "accept", "reviewer": "producer", "note": "ok", "decided_at": "2026-05-13T00:00:00Z"}],
    }))

    assert main(["review", "rebuild", str(session_path), "--timeline", str(timeline_path), "--out", str(out)]) == 0

    rebuilt = json.loads(out.read_text())
    assert rebuilt["operations"][0]["state"] == "accepted"
    assert rebuilt["operations"][0]["provenance"]["manual_review"]["decision"] == "accepted"


def test_report_cli_outputs_html(tmp_path, capsys):
    root = tmp_path / "runs" / "ep1"
    (root / "diff").mkdir(parents=True)
    (root / "exports").mkdir()
    (root / "timeline.accepted.v1.json").write_text(json.dumps({"operations": [], "export_metadata": {}}))
    (root / "diff" / "timeline-diff.json").write_text(json.dumps({"proposed_count": 0, "accepted_count": 0, "rejected_count": 0, "total_removed_duration": 0}))

    assert main(["report", str(root), "--format", "html"]) == 0

    out = capsys.readouterr().out
    assert "<!doctype html>" in out
    assert "Podcast Auto Editor Report" in out


def test_html_report_cli_writes_static_file(tmp_path):
    root = tmp_path / "runs" / "ep1"
    root.mkdir(parents=True)
    out = tmp_path / "report.html"

    assert main(["html-report", str(root), "--out", str(out)]) == 0

    assert out.exists()
    assert "<!doctype html>" in out.read_text()


def test_review_next_cli_outputs_next_operation(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "speech1", "type": "speech_cut", "source_range": {"start": 0.5, "end": 0.75}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "medium", "confidence": 0.8, "provenance": {"detector": "transcript.speech_cleanup_heuristic"}, "preview_ref": "preview/speech1.mp3", "diff_ref": None, "recovery_ref": None})
    timeline_path = tmp_path / "timeline.proposed.v1.json"
    session_path = tmp_path / "review-session.json"
    write_json(timeline_path, timeline)
    write_json(session_path, {"schema_version": "review-session.v1", "source_timeline": str(timeline_path), "decisions": []})

    assert main(["review", "next", str(session_path), "--timeline", str(timeline_path)]) == 0

    out = capsys.readouterr().out
    assert "# Next Review Operation" in out
    assert "speech1" in out
    assert "review decide" in out


def test_review_next_cli_outputs_json(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 1.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline_path = tmp_path / "timeline.proposed.v1.json"
    session_path = tmp_path / "review-session.json"
    write_json(timeline_path, timeline)
    write_json(session_path, {"schema_version": "review-session.v1", "source_timeline": str(timeline_path), "decisions": []})

    assert main(["review", "next", str(session_path), "--timeline", str(timeline_path), "--format", "json"]) == 0

    assert json.loads(capsys.readouterr().out) is None


def test_review_serve_cli_validates_localhost(tmp_path, capsys):
    assert main(["review", "serve", str(tmp_path), "--host", "0.0.0.0"]) == 1
    assert "localhost only" in capsys.readouterr().err


def test_validate_run_cli_accepts_config_timeline_and_transcript(tmp_path, capsys):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"quality": {"min_silence_duration_s": 1.0}}))
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline_path = tmp_path / "timeline.json"
    write_json(timeline_path, timeline)
    transcript_path = tmp_path / "transcript.json"
    transcript_path.write_text(json.dumps({"schema_version": "transcript.v1", "segments": [{"start": 0.0, "end": 1.5, "text": "ok"}]}))

    assert main(["validate-run", "--config", str(config_path), "--timeline", str(timeline_path), "--transcript-json", str(transcript_path)]) == 0

    output = capsys.readouterr().out
    assert "ok" in output
    assert "config" in output
    assert "timeline" in output
    assert "transcript: 1 segment" in output


def test_validate_run_cli_rejects_transcript_beyond_timeline_duration(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 1.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline_path = tmp_path / "timeline.json"
    write_json(timeline_path, timeline)
    transcript_path = tmp_path / "transcript.json"
    transcript_path.write_text(json.dumps([{"start": 0.0, "end": 1.5, "text": "too long"}]))

    assert main(["validate-run", "--timeline", str(timeline_path), "--transcript-json", str(transcript_path)]) == 1

    assert "segment[0] ends after media duration" in capsys.readouterr().err


def test_validate_run_cli_rejects_invalid_config(tmp_path, capsys):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"quality": {"min_silence_duration_s": 0}}))

    assert main(["validate-run", "--config", str(config_path)]) == 1

    assert "min_silence_duration_s must be > 0" in capsys.readouterr().err


def test_validate_run_cli_rejects_invalid_timeline(tmp_path, capsys):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 1.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "bad", "type": "silence_cut", "source_range": {"start": 0.5, "end": 2.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 1.0, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None})
    timeline_path = tmp_path / "timeline.json"
    write_json(timeline_path, timeline)

    assert main(["validate-run", "--timeline", str(timeline_path)]) == 1

    assert "source_range end exceeds media duration" in capsys.readouterr().err


def test_validate_run_cli_duration_override_validates_transcript_only(tmp_path, capsys):
    transcript_path = tmp_path / "transcript.json"
    transcript_path.write_text(json.dumps([{"start": 0.0, "end": 1.5, "text": "too long"}]))

    assert main(["validate-run", "--transcript-json", str(transcript_path), "--duration", "1.0"]) == 1

    assert "segment[0] ends after media duration" in capsys.readouterr().err
