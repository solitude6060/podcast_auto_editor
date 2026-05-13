from podcast_auto_editor.timeline import (
    build_recovery,
    create_noop_timeline,
    kept_segments,
    pts_to_seconds,
    samples_to_seconds,
    seconds_to_pts,
    seconds_to_samples,
    set_operation_state,
    validate_timeline,
)


def make_timeline():
    return create_noop_timeline(
        {"path": "input.wav", "duration": 10.0},
        [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 2}],
    )


def test_timeline_v1_requires_contract_fields():
    timeline = make_timeline()
    assert validate_timeline(timeline) == []
    del timeline["recovery"]
    assert any("missing top-level" in err for err in validate_timeline(timeline))


def test_operation_state_and_risk_validation():
    timeline = make_timeline()
    timeline["operations"].append({"operation_id": "op1", "type": "silence_cut", "source_range": {"start": 1, "end": 2}, "output_range": None, "affected_tracks": ["audio:0"], "state": "done", "risk": "scary", "confidence": 1, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None})
    errors = validate_timeline(timeline)
    assert any("invalid state" in err for err in errors)
    assert any("invalid risk" in err for err in errors)


def test_timeline_validation_rejects_out_of_bounds_track_refs_confidence_and_overlap():
    timeline = make_timeline()
    timeline["operations"] = [
        {"operation_id": "cut1", "type": "silence_cut", "source_range": {"start": 1.0, "end": 3.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "accepted", "risk": "deterministic", "confidence": 1.2, "provenance": {}, "preview_ref": "preview.mp3", "diff_ref": "diff.json", "recovery_ref": "recovery.json"},
        {"operation_id": "cut2", "type": "silence_cut", "source_range": {"start": 2.5, "end": 4.0}, "output_range": None, "affected_tracks": ["missing:0"], "state": "accepted", "risk": "deterministic", "confidence": 1.0, "provenance": {}, "preview_ref": "preview.mp3", "diff_ref": "diff.json", "recovery_ref": "recovery.json"},
        {"operation_id": "cut3", "type": "silence_cut", "source_range": {"start": -0.1, "end": 11.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 0.5, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None},
    ]

    errors = validate_timeline(timeline)

    assert any("confidence must be between 0 and 1" in err for err in errors)
    assert any("unknown affected track" in err for err in errors)
    assert any("source_range start must be >= 0" in err for err in errors)
    assert any("source_range end exceeds media duration" in err for err in errors)
    assert any("accepted cut overlaps" in err for err in errors)


def test_timebase_conversions_round_trip():
    assert seconds_to_samples(1.5, 48000) == 72000
    assert samples_to_seconds(72000, 48000) == 1.5
    assert seconds_to_pts(0.1, "1/30000") == 3000
    assert pts_to_seconds(3000, "1/30000") == 0.1


def test_recovery_map_accounts_for_accepted_cuts_only():
    timeline = make_timeline()
    timeline["operations"] = [
        {"operation_id": "cut1", "type": "silence_cut", "source_range": {"start": 2.0, "end": 3.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "accepted", "risk": "deterministic", "confidence": 1.0, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None},
        {"operation_id": "cut2", "type": "silence_cut", "source_range": {"start": 5.0, "end": 6.0}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 1.0, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None},
    ]
    recovery = build_recovery(timeline)
    assert recovery["removed_segments"] == [{"operation_id": "cut1", "source_start": 2.0, "source_end": 3.0, "duration": 1.0}]
    assert recovery["source_to_output"][1] == {"source_start": 3.0, "source_end": 10.0, "output_start": 2.0, "output_end": 9.0}


def test_kept_segments_identity_for_no_cuts():
    assert kept_segments(3.0, []) == [{"source_start": 0.0, "source_end": 3.0, "output_start": 0.0, "output_end": 3.0}]


def test_set_operation_state_accepts_all_when_no_ids():
    timeline = make_timeline()
    timeline["operations"] = [{"operation_id": "cut1", "type": "silence_cut", "source_range": {"start": 1, "end": 2}, "output_range": None, "affected_tracks": ["audio:0"], "state": "proposed", "risk": "deterministic", "confidence": 1, "provenance": {}, "preview_ref": None, "diff_ref": None, "recovery_ref": None}]
    accepted = set_operation_state(timeline, None, "accepted")
    assert accepted["operations"][0]["state"] == "accepted"
    assert accepted["recovery"]["removed_segments"][0]["operation_id"] == "cut1"
