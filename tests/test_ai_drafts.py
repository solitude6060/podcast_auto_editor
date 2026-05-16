from __future__ import annotations

import json
from pathlib import Path

import pytest

from podcast_auto_editor.ai_drafts import SCHEMA_VERSION, build_ai_explanation, generate_ai_draft
from podcast_auto_editor.timeline import create_noop_timeline


def _timeline_with_operations():
    timeline = create_noop_timeline(
        {"path": "input.wav", "duration": 10.0},
        [{"track_id": "audio:0", "type": "audio", "sample_rate": 48000, "channels": 1}],
    )
    timeline["operations"].extend(
        [
            {
                "operation_id": "retake1",
                "type": "retake_cut",
                "state": "proposed",
                "source_range": {"start": 1.0, "end": 1.5},
            },
            {
                "operation_id": "speech1",
                "type": "speech_cut",
                "state": "proposed",
                "source_range": {"start": 2.0, "end": 2.6},
            },
            {
                "operation_id": "silence1",
                "type": "silence_cut",
                "state": "proposed",
                "source_range": {"start": 4.0, "end": 4.3},
            },
        ]
    )
    return timeline


def test_generate_ai_draft_requires_transcript():
    timeline = _timeline_with_operations()

    with pytest.raises(ValueError, match="transcript segments are required"):
        generate_ai_draft(
            timeline=timeline,
            transcript_segments=[],
            dry_prompt=True,
        )


def test_generate_ai_draft_dry_prompt_builds_payload_and_limits_candidates(monkeypatch):
    timeline = _timeline_with_operations()
    transcript_segments = [{"start": 0.0, "end": 0.4, "text": "hi there"}]
    called = {"count": 0}

    def never_call(*_args, **_kwargs):  # pragma: no cover - network hard-stop guard
        called["count"] += 1
        raise AssertionError("chat_with_local_ai must not be called in dry-prompt mode")

    monkeypatch.setattr("podcast_auto_editor.ai_drafts.chat_with_local_ai", never_call)
    payload = generate_ai_draft(
        timeline=timeline,
        transcript_segments=transcript_segments,
        dry_prompt=True,
        no_net=True,
        base_url="http://example.local",
        model="draft-model",
        max_chapters=3,
        timeline_path=Path("runs/episode/timeline.proposed.v1.json"),
    )

    assert called["count"] == 0
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["dry_prompt"] is True
    assert payload["request"]["model"] == "draft-model"
    assert payload["metadata"]["candidate_operation_count"] == 2
    assert payload["request"]["messages"][1]["content"].count("retake1") == 1


def test_generate_ai_draft_normalizes_live_response(monkeypatch):
    timeline = _timeline_with_operations()
    transcript_segments = [{"start": 0.0, "end": 0.4, "text": "hi there"}]

    def fake_chat_with_local_ai(**_kwargs) -> str:
        return json.dumps(
            {
                "chapters": [
                    {"title": "Intro", "start": 0.0, "end": 3.0, "why_merged": "tight opening"},
                ],
                "summary": {
                    "title": "Episode summary",
                    "one_paragraph": "Short summary",
                    "key_points": ["point one", "point two"],
                },
                "show_notes": ["Cleaned speech", ""],
                "retake_decisions": [
                    {
                        "operation_id": "retake1",
                        "suggested_action": "probably_delete",
                        "rationale": "duplicated phrase",
                        "confidence": 1.2,
                        "reasoning": "high duplication",
                    },
                    {"operation_id": "missing", "suggested_action": "skip"},
                ],
                "operation_explanations": [
                    {"operation_id": "speech1", "why_risky": "filler", "llm_reason": "speech quality"},
                ],
            }
        )

    monkeypatch.setattr("podcast_auto_editor.ai_drafts.chat_with_local_ai", fake_chat_with_local_ai)
    payload = generate_ai_draft(
        timeline=timeline,
        transcript_segments=transcript_segments,
        max_chapters=2,
        no_net=False,
    )

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["chapters"][0]["index"] == 1
    assert payload["chapters"][0]["title"] == "Intro"
    assert payload["summary"]["title"] == "Episode summary"
    assert payload["show_notes"] == ["Cleaned speech"]
    assert payload["retake_decisions"][0]["operation_id"] == "retake1"
    assert payload["retake_decisions"][0]["suggested_action"] == "probably_delete"
    assert payload["retake_decisions"][0]["confidence"] == 1.0
    assert payload["retake_decisions"][0]["operation_known"] is True
    assert payload["operation_explanations"][0]["operation_known"] is True


def test_ai_draft_prompt_omits_speakers_when_segments_absent(monkeypatch):
    """Backward compatibility: existing transcripts without speaker_segments
    must produce the same prompt shape as before PR-D (no Speakers line)."""
    timeline = _timeline_with_operations()
    transcript_segments = [{"start": 0.0, "end": 0.4, "text": "hi there"}]

    monkeypatch.setattr(
        "podcast_auto_editor.ai_drafts.chat_with_local_ai",
        lambda **_k: (_ for _ in ()).throw(AssertionError("must not call network in dry-prompt")),
    )

    payload = generate_ai_draft(
        timeline=timeline,
        transcript_segments=transcript_segments,
        dry_prompt=True,
    )
    user_content = payload["request"]["messages"][1]["content"]
    assert "Speakers:" not in user_content


def test_ai_draft_prompt_includes_speaker_segments_when_present(monkeypatch):
    """PR-D contract: when speaker_segments are supplied, the prompt names
    each speaker so the LLM can attribute chapters / show-notes correctly."""
    timeline = _timeline_with_operations()
    transcript_segments = [{"start": 0.0, "end": 4.0, "text": "hello and welcome"}]
    speaker_segments = [
        {"start": 0.0, "end": 2.0, "speaker_id": "spk0", "confidence": 0.95},
        {"start": 2.0, "end": 4.0, "speaker_id": "spk1", "confidence": 0.92},
    ]

    monkeypatch.setattr(
        "podcast_auto_editor.ai_drafts.chat_with_local_ai",
        lambda **_k: (_ for _ in ()).throw(AssertionError("must not call network in dry-prompt")),
    )

    payload = generate_ai_draft(
        timeline=timeline,
        transcript_segments=transcript_segments,
        speaker_segments=speaker_segments,
        dry_prompt=True,
    )
    user_content = payload["request"]["messages"][1]["content"]
    assert "Speakers:" in user_content
    assert "spk0" in user_content
    assert "spk1" in user_content
    # metadata should mark speakers were used
    assert payload["metadata"]["speaker_count"] == 2


def test_ai_draft_prompt_honors_speaker_labels_override(monkeypatch):
    """Users can supply human-friendly labels for the prompt via
    `speaker_labels={"spk0": "Host", "spk1": "Guest"}`. The labels are
    rendered into the prompt; the speaker_id remains the canonical id."""
    timeline = _timeline_with_operations()
    transcript_segments = [{"start": 0.0, "end": 4.0, "text": "hi"}]
    speaker_segments = [
        {"start": 0.0, "end": 2.0, "speaker_id": "spk0", "confidence": 0.95},
        {"start": 2.0, "end": 4.0, "speaker_id": "spk1", "confidence": 0.92},
    ]

    monkeypatch.setattr(
        "podcast_auto_editor.ai_drafts.chat_with_local_ai",
        lambda **_k: (_ for _ in ()).throw(AssertionError("must not call network in dry-prompt")),
    )

    payload = generate_ai_draft(
        timeline=timeline,
        transcript_segments=transcript_segments,
        speaker_segments=speaker_segments,
        speaker_labels={"spk0": "Host", "spk1": "Guest"},
        dry_prompt=True,
    )
    user_content = payload["request"]["messages"][1]["content"]
    assert "Host" in user_content
    assert "Guest" in user_content


def test_ai_draft_normalized_chapters_preserve_speaker_id(monkeypatch):
    """When the LLM returns chapter objects with speaker_id, the
    normalized payload retains the field (None if the LLM omits it).
    Backward compat: chapters without speaker_id stay parseable."""
    timeline = _timeline_with_operations()
    transcript_segments = [{"start": 0.0, "end": 0.4, "text": "hi"}]

    def fake_chat(**_k):
        return json.dumps({
            "chapters": [
                {"title": "Intro", "start": 0.0, "end": 2.0, "why_merged": "host intro", "speaker_id": "spk0"},
                {"title": "Topic", "start": 2.0, "end": 5.0, "why_merged": "guest answer"},
            ],
            "summary": {"title": "ep", "one_paragraph": "x", "key_points": []},
            "show_notes": [],
            "retake_decisions": [],
            "operation_explanations": [],
        })

    monkeypatch.setattr("podcast_auto_editor.ai_drafts.chat_with_local_ai", fake_chat)

    payload = generate_ai_draft(
        timeline=timeline,
        transcript_segments=transcript_segments,
        no_net=False,
        dry_prompt=False,
    )
    assert payload["chapters"][0]["speaker_id"] == "spk0"
    assert payload["chapters"][1].get("speaker_id") is None


def test_build_ai_explanation_dry_prompt_includes_payload():
    timeline = _timeline_with_operations()

    result = build_ai_explanation(
        timeline=timeline,
        operation_id="speech1",
        transcript_segments=[{"start": 0.0, "end": 0.4, "text": "hi there"}],
        dry_prompt=True,
        no_net=True,
        base_url="http://example.local",
        model="explain-model",
    )

    assert result["schema_version"] == SCHEMA_VERSION
    assert result["operation_id"] == "speech1"
    assert result["ai_explanation"]["dry_prompt"] is True
    assert result["ai_explanation"]["request"]["model"] == "explain-model"


def test_build_ai_explanation_raises_for_unknown_operation():
    timeline = _timeline_with_operations()

    with pytest.raises(ValueError, match="operation missing was not found"):
        build_ai_explanation(
            timeline=timeline,
            operation_id="missing",
            transcript_segments=[],
            dry_prompt=True,
        )
