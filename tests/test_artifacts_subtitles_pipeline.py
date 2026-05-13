import json
import tempfile
from pathlib import Path

import pytest

from podcast_auto_editor.artifacts import run_paths, write_diff_artifacts
from podcast_auto_editor.config import load_config
from podcast_auto_editor.media import MediaToolError
from podcast_auto_editor.pipeline import accept_all, remap_cues_to_output, retake_operation_is_render_safe, transcribe_and_write, write_preview
from podcast_auto_editor.subtitles import cues_to_srt, cues_to_vtt, heuristic_chapters, validate_chapters, validate_cues
from podcast_auto_editor.timeline import create_noop_timeline


def test_artifact_paths_are_episode_scoped_and_reject_traversal():
    paths = run_paths("runs", "episode-1")
    assert str(paths.proposed_timeline).endswith("runs/episode-1/timeline.proposed.v1.json")
    assert str(paths.timeline_diff).endswith("runs/episode-1/diff/timeline-diff.json")
    with pytest.raises(ValueError):
        run_paths("runs", "../evil")


def test_srt_and_vtt_format_and_validation():
    cues = [{"start": 0.0, "end": 1.25, "text": "hello"}, {"start": 2.0, "end": 3.0, "text": "world"}]
    assert "00:00:01,250" in cues_to_srt(cues)
    assert "WEBVTT" in cues_to_vtt(cues)
    assert "00:00:01.250" in cues_to_vtt(cues)
    assert validate_cues(cues, duration=3.0) == []
    assert validate_cues([{"start": 2, "end": 1, "text": "bad"}], duration=3.0)


def test_chapters_are_monotonic_in_bounds_and_heuristic():
    cues = [{"start": 0, "end": 1, "text": "opening"}, {"start": 301, "end": 302, "text": "new topic"}]
    chapters = heuristic_chapters(cues, duration=600, min_chapter_s=300)
    assert len(chapters) == 2
    assert validate_chapters(chapters, 600) == []
    chapters[1]["start"] = 700
    assert validate_chapters(chapters, 600)


def test_accept_all_adds_refs_and_recovery():
    timeline = create_noop_timeline({"path": "input.wav", "duration": 5.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "cut1", "type": "silence_cut", "source_range": {"start": 1.0, "end": 2.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 1.0, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None})
    accepted = accept_all(timeline)
    op = accepted["operations"][0]
    assert op["state"] == "accepted"
    assert op["preview_ref"]
    assert accepted["recovery"]["removed_segments"][0]["operation_id"] == "cut1"


def test_diff_artifacts_include_human_summary_and_removed_segment_metadata(tmp_path):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 5.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append(
        {
            "operation_id": "cut1",
            "type": "silence_cut",
            "source_range": {"start": 1.0, "end": 2.5},
            "output_range": None,
            "affected_tracks": ["audio:0"],
            "state": "proposed",
            "risk": "deterministic",
            "confidence": 1.0,
            "provenance": {"silence": {"threshold_db": -50}},
            "preview_ref": None,
            "diff_ref": None,
            "recovery_ref": None,
        }
    )
    accepted = accept_all(timeline)
    paths = run_paths(tmp_path, "ep1")

    write_diff_artifacts(paths, timeline, accepted)

    diff = json.loads(paths.timeline_diff.read_text())
    removed = json.loads(paths.removed_segments.read_text())
    summary = paths.human_summary.read_text()
    assert diff["total_removed_duration"] == 1.5
    assert diff["removed_segments"][0]["operation_type"] == "silence_cut"
    assert removed[0]["preview_ref"] == "preview/before-after-preview.mp3"
    assert removed[0]["reason"] == "silence below -50 dB"
    assert "| cut1 | silence_cut | 1.000s–2.500s | 1.500s | deterministic | 1.00 | preview/before-after-preview.mp3 | silence below -50 dB |" in summary


def test_preview_metadata_records_removed_segment_preview_manifest(tmp_path):
    timeline = create_noop_timeline({"path": "input.wav", "duration": 5.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append(
        {
            "operation_id": "cut1",
            "type": "silence_cut",
            "source_range": {"start": 1.0, "end": 2.5},
            "output_range": None,
            "affected_tracks": ["audio:0"],
            "state": "accepted",
            "risk": "deterministic",
            "confidence": 1.0,
            "provenance": {},
            "preview_ref": "preview/before-after-preview.mp3",
            "diff_ref": "diff/timeline-diff.json",
            "recovery_ref": "recovery/recovery-map.json",
        }
    )
    paths = run_paths(tmp_path, "ep1")

    with pytest.raises(MediaToolError):
        write_preview(paths, tmp_path / "missing.wav", timeline)

    metadata = json.loads(paths.waveform.read_text())
    preview = metadata["removed_segments_preview"]
    assert preview["path"].endswith("preview/removed-segments-preview.mp3")
    assert preview["segment_count"] == 1
    assert preview["total_duration"] == 1.5
    assert preview["segments"][0]["operation_id"] == "cut1"


def test_transcribe_and_write_creates_required_assets():
    timeline = create_noop_timeline({"path": "input.wav", "duration": 2.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    with tempfile.TemporaryDirectory() as td:
        paths = run_paths(Path(td), "ep1")
        transcribe_and_write(paths, timeline, cues=[{"start": 0.0, "end": 1.0, "text": "hello"}])
        assert paths.transcript.exists()
        assert paths.subtitles_srt.exists()
        assert paths.subtitles_vtt.exists()
        assert paths.chapters.exists()


def test_remap_cues_to_output_shifts_drops_and_splits_by_recovery_map():
    cues = [
        {"start": 0.5, "end": 1.0, "text": "before"},
        {"start": 2.2, "end": 2.8, "text": "removed"},
        {"start": 1.5, "end": 3.5, "text": "spans cut"},
        {"start": 4.0, "end": 5.0, "text": "after"},
    ]
    recovery = {
        "source_to_output": [
            {"source_start": 0.0, "source_end": 2.0, "output_start": 0.0, "output_end": 2.0},
            {"source_start": 3.0, "source_end": 6.0, "output_start": 2.0, "output_end": 5.0},
        ]
    }

    assert remap_cues_to_output(cues, recovery) == [
        {"start": 0.5, "end": 1.0, "text": "before"},
        {"start": 1.5, "end": 2.0, "text": "spans cut"},
        {"start": 2.0, "end": 2.5, "text": "spans cut"},
        {"start": 3.0, "end": 4.0, "text": "after"},
    ]


def test_transcribe_and_write_uses_output_timestamps_after_cut():
    timeline = create_noop_timeline({"path": "input.wav", "duration": 5.0}, [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}])
    timeline["operations"].append({"operation_id": "cut1", "type": "silence_cut", "source_range": {"start": 1.0, "end": 2.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "accepted", "risk": "deterministic", "confidence": 1.0, "provenance": {}, "preview_ref": "preview.mp3", "diff_ref": "diff.json", "recovery_ref": "recovery.json"})
    timeline = accept_all(timeline)
    with tempfile.TemporaryDirectory() as td:
        paths = run_paths(Path(td), "ep1")
        transcribe_and_write(paths, timeline, cues=[{"start": 3.0, "end": 4.0, "text": "after cut"}])
        assert '"start": 2.0' in paths.transcript.read_text()
        assert "00:00:02,000" in paths.subtitles_srt.read_text()


def test_quality_missing_clipping_metric_fails():
    from podcast_auto_editor.quality import evaluate_quality
    report = evaluate_quality({"integrated_lufs": -16.0, "true_peak_db": -2.0}, 2, load_config().quality)
    assert report["passed"] is False
    assert [c for c in report["checks"] if c["name"] == "clipped_samples"][0]["passed"] is False


def test_retake_render_safety_accepts_manual_review_provenance_only_when_complete():
    op = {
        "type": "retake_cut",
        "state": "accepted",
        "provenance": {"manual_review": {"decision": "accepted", "reviewer": "producer", "reviewed_at": "2026-05-12T00:00:00Z"}},
    }
    assert retake_operation_is_render_safe(op) is True

    op["provenance"]["manual_review"]["reviewer"] = ""
    assert retake_operation_is_render_safe(op) is False
