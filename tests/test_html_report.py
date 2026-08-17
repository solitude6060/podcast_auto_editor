import json

from podcast_auto_editor.html_report import build_html_report


def test_build_html_report_escapes_values_and_links_artifacts(tmp_path):
    root = tmp_path / "runs" / "ep1"
    (root / "diff").mkdir(parents=True)
    (root / "preview" / "operations" / "cut1").mkdir(parents=True)
    (root / "recovery").mkdir()
    (root / "exports").mkdir()
    (root / "timeline.accepted.v1.json").write_text(json.dumps({
        "operations": [{
            "operation_id": "cut<1>",
            "type": "speech_cut",
            "source_range": {"start": 1.0, "end": 1.5},
            "state": "proposed",
            "risk": "medium",
            "confidence": 0.8,
            "provenance": {"detector": "transcript<&>detector"},
            "preview_ref": "preview/operations/cut1/before-after.mp3",
            "diff_ref": "diff/timeline-diff.json",
            "recovery_ref": "recovery/recovery-map.json",
        }],
        "export_metadata": {
            "export_profiles": [{"name": "podcast-stereo", "path": str(root / "exports" / "episode.podcast-stereo.mp3"), "quality_gate_report": {"passed": True}}],
            "derived_assets": {"cue_errors": ["needs <escape>"]},
        },
    }))
    (root / "diff" / "timeline-diff.json").write_text(json.dumps({"proposed_count": 1, "accepted_count": 0, "rejected_count": 0, "total_removed_duration": 0.0}))

    html = build_html_report(root)

    assert "<!doctype html>" in html
    assert "cut&lt;1&gt;" in html
    assert "transcript&lt;&amp;&gt;detector" in html
    assert "needs &lt;escape&gt;" in html
    assert 'href="preview/operations/cut1/before-after.mp3"' in html
    assert 'href="diff/timeline-diff.json"' in html
    assert 'href="recovery/recovery-map.json"' in html
    assert 'href="exports/episode.podcast-stereo.mp3"' in html


def test_build_html_report_surfaces_profile_quality_details(tmp_path):
    root = tmp_path / "runs" / "ep1"
    (root / "diff").mkdir(parents=True)
    (root / "exports").mkdir()
    (root / "timeline.accepted.v1.json").write_text(json.dumps({
        "operations": [],
        "export_metadata": {
            "export_profiles": [
                {
                    "name": "podcast-stereo",
                    "path": str(root / "exports" / "episode.podcast-stereo.mp3"),
                    "quality_gate_report": {
                        "passed": False,
                        "checks": [{"name": "loudness", "passed": False, "target": -16.0, "actual": -17.3}],
                    },
                }
            ],
            "failed_quality_profile": {"name": "podcast-stereo", "failed_checks": ["loudness"]},
        },
    }))
    (root / "diff" / "timeline-diff.json").write_text(json.dumps({"proposed_count": 0, "accepted_count": 0, "rejected_count": 0, "total_removed_duration": 0.0}))

    html = build_html_report(root)

    assert "podcast-stereo" in html
    assert "failed" in html
    assert "loudness" in html
    assert "-17.3" in html


def test_build_html_report_handles_missing_timeline(tmp_path):
    root = tmp_path / "runs" / "ep1"
    root.mkdir(parents=True)

    html = build_html_report(root)

    assert "Operations: 0" in html
    assert "not measured" in html


def test_html_report_groups_operations_and_links_review_session(tmp_path):
    root = tmp_path / "runs" / "ep1"
    (root / "diff").mkdir(parents=True)
    (root / "exports").mkdir()
    (root / "review-session.json").write_text(json.dumps({
        "schema_version": "review-session.v1",
        "source_timeline": "timeline.proposed.v1.json",
        "decisions": [
            {"operation_id": "speech1", "decision": "accept", "reviewer": "producer", "note": "ok", "decided_at": "2026-05-13T00:00:00Z"},
            {"operation_id": "silence1", "decision": "undo", "reviewer": "producer", "note": "defer", "decided_at": "2026-05-13T00:01:00Z"},
        ],
    }))
    (root / "timeline.accepted.v1.json").write_text(json.dumps({
        "operations": [
            {"operation_id": "speech1", "type": "speech_cut", "source_range": {"start": 1.0, "end": 1.5}, "state": "proposed", "risk": "medium", "confidence": 0.8, "provenance": {"detector": "transcript.speech_cleanup_heuristic"}, "preview_ref": "preview/speech1.mp3", "diff_ref": None, "recovery_ref": None},
            {"operation_id": "silence1", "type": "silence_cut", "source_range": {"start": 3.0, "end": 4.0}, "state": "accepted", "risk": "deterministic", "confidence": 1.0, "provenance": {"detector": "ffmpeg.silencedetect"}, "preview_ref": "preview/silence1.mp3", "diff_ref": None, "recovery_ref": None},
        ],
        "export_metadata": {},
    }))
    (root / "diff" / "timeline-diff.json").write_text(json.dumps({"proposed_count": 2, "accepted_count": 1, "rejected_count": 0, "total_removed_duration": 1.0}))

    html = build_html_report(root)

    assert "Operation groups" in html
    assert "medium: 1" in html
    assert "deterministic: 1" in html
    assert "transcript.speech_cleanup_heuristic: 1" in html
    assert "ffmpeg.silencedetect: 1" in html
    assert "Review session" in html
    assert 'href="review-session.json"' in html
    assert "Accepted: 1" in html
    assert "Undone: 1" in html
    assert 'class="manual-review-required"' in html
    assert "Manual review required" in html
