import json

from podcast_auto_editor.cli import main
from podcast_auto_editor.transcript import TranscriptValidationError, normalize_transcript_segments


def test_transcript_v1_accepts_optional_speaker_id():
    """PR-C contract: transcript cues may carry a `speaker_id` field for
    downstream per-speaker processing (PR-D AI draft attribution,
    PR-E per-speaker filler detection). The field is optional and
    preserved through validation."""
    segments = normalize_transcript_segments([
        {"start": 0.0, "end": 1.0, "text": "hi there", "speaker_id": "spk0"},
        {"start": 1.0, "end": 2.0, "text": "hello back", "speaker_id": "spk1"},
    ])
    assert segments[0]["speaker_id"] == "spk0"
    assert segments[1]["speaker_id"] == "spk1"


def test_transcript_v1_validation_passes_without_speaker_id():
    """Backward compatibility: existing transcripts without `speaker_id`
    must continue to validate. The field stays optional, not required."""
    segments = normalize_transcript_segments([
        {"start": 0.0, "end": 1.0, "text": "hi"},
    ])
    assert segments[0]["start"] == 0.0
    assert "speaker_id" not in segments[0]


def test_normalize_transcript_accepts_segments_object_and_preserves_metadata():
    segments = normalize_transcript_segments({
        "segments": [
            {"start": "0", "end": 1.25, "text": "hello", "speaker": "host"},
            {"start": 1.25, "end": 2.0, "text": "world"},
        ]
    })

    assert segments == [
        {"start": 0.0, "end": 1.25, "text": "hello", "speaker": "host"},
        {"start": 1.25, "end": 2.0, "text": "world"},
    ]


def test_normalize_transcript_rejects_overlaps():
    try:
        normalize_transcript_segments([
            {"start": 0.0, "end": 2.0, "text": "first"},
            {"start": 1.5, "end": 3.0, "text": "overlap"},
        ])
    except TranscriptValidationError as exc:
        assert "overlaps previous segment" in str(exc)
    else:
        raise AssertionError("expected transcript validation failure")


def test_validate_transcript_cli_reports_segment_count(tmp_path, capsys):
    path = tmp_path / "transcript.json"
    path.write_text(json.dumps({"segments": [{"start": 0, "end": 1, "text": "ok"}]}))

    assert main(["validate-transcript", str(path)]) == 0
    assert "ok (1 segments)" in capsys.readouterr().out


def test_validate_transcript_cli_rejects_malformed_json(tmp_path, capsys):
    path = tmp_path / "transcript.json"
    path.write_text('{"segments": [')

    assert main(["validate-transcript", str(path)]) == 1
    assert "invalid transcript JSON" in capsys.readouterr().err


def test_run_cli_rejects_invalid_transcript_before_pipeline(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"segments": [{"start": 0, "end": 0, "text": "bad"}]}))

    assert main(["run", str(tmp_path / "missing.wav"), "--out", str(tmp_path / "runs"), "--transcript-json", str(path)]) == 1
    assert "end must be after start" in capsys.readouterr().err
