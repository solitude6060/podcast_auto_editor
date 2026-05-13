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


def test_build_html_report_handles_missing_timeline(tmp_path):
    root = tmp_path / "runs" / "ep1"
    root.mkdir(parents=True)

    html = build_html_report(root)

    assert "Operations: 0" in html
    assert "not measured" in html
