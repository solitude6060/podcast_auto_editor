import tempfile
from pathlib import Path

import pytest

from podcast_auto_editor.artifacts import run_paths
from podcast_auto_editor.config import load_config
from podcast_auto_editor.pipeline import accept_all, remap_cues_to_output, retake_operation_is_render_safe, transcribe_and_write
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
