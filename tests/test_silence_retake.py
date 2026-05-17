from dataclasses import replace

from podcast_auto_editor.config import load_config
from podcast_auto_editor.retake import detect_retake_candidates, detect_speech_cleanup_candidates, may_auto_accept_retake
from podcast_auto_editor.silence import propose_silence_cuts


def test_silence_cut_retains_padding_and_records_provenance():
    cfg = load_config().quality
    ops = propose_silence_cuts([{"start": 5.0, "end": 7.0}], cfg)
    assert len(ops) == 1
    op = ops[0]
    assert op["source_range"] == {"start": 5.25, "end": 6.75, "unit": "seconds"}
    assert op["risk"] == "deterministic"
    assert op["state"] == "proposed"
    assert op["provenance"]["speech_padding_s"] == 0.25


def test_short_silence_does_not_create_cut():
    cfg = load_config().quality
    assert propose_silence_cuts([{"start": 0.0, "end": 1.499}], cfg) == []


def test_explicit_retake_marker_creates_low_risk_proposed_candidate():
    cfg = load_config().retake
    transcript = [
        {"start": 1.0, "end": 3.0, "text": "This is the bad version"},
        {"start": 3.0, "end": 4.0, "text": "Let me say that again"},
    ]
    ops = detect_retake_candidates(transcript, cfg)
    assert len(ops) == 1
    assert ops[0]["risk"] == "low"
    assert ops[0]["state"] == "proposed"
    assert ops[0]["confidence"] >= 0.90


def test_near_duplicate_phrase_creates_candidate():
    cfg = load_config().retake
    transcript = [
        {"start": 1.0, "end": 3.0, "text": "Welcome to this podcast episode"},
        {"start": 4.0, "end": 6.0, "text": "Welcome to this podcast episode"},
    ]
    assert detect_retake_candidates(transcript, cfg)[0]["provenance"]["reason"] == "near_duplicate"


def test_low_risk_speech_not_auto_accepted_when_disabled():
    cfg = load_config().retake
    op = detect_retake_candidates([
        {"start": 1, "end": 2, "text": "bad take"},
        {"start": 2, "end": 3, "text": "start again"},
    ], cfg)[0]
    accepted, reason = may_auto_accept_retake(op, cfg, artifacts_exist=True)
    assert accepted is False
    assert "disabled" in reason


def test_auto_accept_requires_all_gates():
    base = load_config().retake
    cfg = replace(base, auto_low_risk_speech=True)
    op = detect_retake_candidates([
        {"start": 1, "end": 2, "text": "bad take"},
        {"start": 2, "end": 3, "text": "start again"},
    ], cfg)[0]
    assert may_auto_accept_retake(op, cfg, artifacts_exist=True) == (True, "accepted by low-risk retake policy")
    op["confidence"] = 0.899
    accepted, reason = may_auto_accept_retake(op, cfg, artifacts_exist=True)
    assert accepted is False
    assert "confidence" in reason


def test_filler_and_false_start_create_proposed_speech_cleanup_candidates():
    ops = detect_speech_cleanup_candidates([
        {"start": 1.0, "end": 1.4, "text": "um"},
        {"start": 2.0, "end": 2.8, "text": "I was going to--"},
        {"start": 3.0, "end": 4.0, "text": "actual content"},
    ])

    assert [op["type"] for op in ops] == ["speech_cut", "speech_cut"]
    assert all(op["state"] == "proposed" for op in ops)
    assert all(op["risk"] == "medium" for op in ops)
    assert ops[0]["provenance"]["reason"] == "filler"
    assert ops[1]["provenance"]["reason"] == "false_start"


def test_speech_cleanup_per_speaker_aggression_off_skips_speaker():
    """PR-E: when a per-speaker aggression map sets a speaker to "off",
    that speaker's cues are not flagged as filler / false-start. Cues
    without speaker_id, or with speakers not in the map, use the default
    behaviour."""
    ops = detect_speech_cleanup_candidates(
        [
            {"start": 1.0, "end": 1.4, "text": "um", "speaker_id": "spk0"},
            {"start": 2.0, "end": 2.4, "text": "um", "speaker_id": "spk1"},
            {"start": 3.0, "end": 3.4, "text": "um"},
        ],
        speaker_aggression={"spk0": "off"},
    )

    assert len(ops) == 2
    speakers = [op["provenance"].get("speaker_id") for op in ops]
    assert "spk0" not in speakers
    assert "spk1" in speakers


def test_backchannel_detection_emits_backchannel_cut_type():
    """PR-E: backchannel utterances (right / mhm / 對對對) are a distinct
    proposed-only operation type (`backchannel_cut`), separate from `speech_cut`."""
    from podcast_auto_editor.retake import detect_backchannel_candidates

    ops = detect_backchannel_candidates([
        {"start": 1.0, "end": 1.2, "text": "right"},
        {"start": 2.0, "end": 2.2, "text": "mhm"},
        {"start": 3.0, "end": 3.4, "text": "對對對"},
        {"start": 4.0, "end": 6.0, "text": "this is real content"},
    ])

    assert [op["type"] for op in ops] == ["backchannel_cut", "backchannel_cut", "backchannel_cut"]
    assert all(op["state"] == "proposed" for op in ops)
    assert all(op["provenance"]["detector"] == "transcript.backchannel_heuristic" for op in ops)


def test_backchannel_detection_respects_per_speaker_aggression():
    from podcast_auto_editor.retake import detect_backchannel_candidates

    ops = detect_backchannel_candidates(
        [
            {"start": 1.0, "end": 1.2, "text": "right", "speaker_id": "spk0"},
            {"start": 2.0, "end": 2.2, "text": "right", "speaker_id": "spk1"},
        ],
        speaker_aggression={"spk0": "off"},
    )

    assert len(ops) == 1
    assert ops[0]["provenance"]["speaker_id"] == "spk1"


def test_timeline_validates_accepted_backchannel_cut_requires_artifacts():
    """`backchannel_cut` is a speech-changing op; accepting it without
    preview/diff/recovery artefacts must be rejected by validate_timeline,
    same discipline as speech_cut/retake_cut."""
    from podcast_auto_editor.timeline import create_noop_timeline, validate_timeline

    timeline = create_noop_timeline(
        {"path": "input.wav", "duration": 5.0},
        [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}],
    )
    timeline["operations"].append({
        "operation_id": "bc1",
        "type": "backchannel_cut",
        "source_range": {"start": 1.0, "end": 1.2},
        "output_range": None,
        "affected_tracks": ["audio:0"],
        "state": "accepted",
        "risk": "medium",
        "confidence": 0.9,
        "provenance": {"detector": "transcript.backchannel_heuristic"},
        "preview_ref": None,
        "diff_ref": None,
        "recovery_ref": None,
    })

    errors = validate_timeline(timeline)
    assert any("preview_ref" in err for err in errors), errors
