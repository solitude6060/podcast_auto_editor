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
