from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .explain import explain_operation

SCHEMA_VERSION = "ai-draft.v1"
AI_DRAFT_REL_PATH = "ai/ai-draft.v1.json"
DEFAULT_TIMEOUT_SECONDS = 0.5


class AIServiceError(RuntimeError):
    """Raised when local AI request/response cannot be used."""


def _coerce_confidence(value: object) -> float:
    if value is None:
        return 0.0
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    if confidence < 0.0:
        return 0.0
    if confidence > 1.0:
        return 1.0
    return confidence


def _default_base_url() -> str:
    return os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:9090/v1")


def _default_model() -> str:
    return os.getenv("LOCAL_LLM_MODEL", "qwen3.6-27b-turbo3")


def _default_timeout() -> float:
    return DEFAULT_TIMEOUT_SECONDS


def _transcript_excerpt(segments: list[dict[str, Any]], max_chars: int = 3500) -> str:
    if not segments:
        return ""
    parts: list[str] = []
    for segment in segments:
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start))
        parts.append(f"[{start:.3f}-{end:.3f}] {text}")
    joined = "\n".join(parts)
    if len(joined) <= max_chars:
        return joined
    return joined[:max_chars].rstrip() + "..."


def _build_payload_json(*, model: str, prompt: str, max_tokens: int = 768) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict podcast editor assistant. "
                    "Return strict JSON only that matches the requested schema. "
                    "No markdown, no commentary."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }


def _operation_payloads(operations: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for operation in operations or []:
        source = operation.get("source_range") or {}
        output.append(
            {
                "operation_id": str(operation.get("operation_id")),
                "type": str(operation.get("type")),
                "risk": operation.get("risk"),
                "confidence": _coerce_confidence(operation.get("confidence")),
                "source_start": source.get("start"),
                "source_end": source.get("end"),
            }
        )
    return output


def _format_speakers_block(speaker_segments: list[dict[str, Any]] | None, speaker_labels: dict[str, str] | None) -> str:
    """Build the optional 'Speakers:' prompt block from speaker_segments + labels."""
    if not speaker_segments:
        return ""
    seen: dict[str, str] = {}
    for seg in speaker_segments:
        spk = str(seg.get("speaker_id", "")).strip()
        if not spk or spk in seen:
            continue
        label = (speaker_labels or {}).get(spk, spk)
        seen[spk] = label
    if not seen:
        return ""
    lines = [f"- {spk} = {label}" for spk, label in seen.items()]
    return "Speakers:\n" + "\n".join(lines) + "\n\n"


def _build_draft_prompt(
    *,
    transcript_segments: list[dict[str, Any]],
    operation_payloads: list[dict[str, Any]],
    max_chapters: int,
    speaker_segments: list[dict[str, Any]] | None = None,
    speaker_labels: dict[str, str] | None = None,
) -> str:
    transcript = _transcript_excerpt(transcript_segments)
    operation_context = json.dumps(operation_payloads, ensure_ascii=False, indent=2)
    speakers_block = _format_speakers_block(speaker_segments, speaker_labels)
    chapter_schema_hint = (
        "title/start/end/why_merged/speaker_id (speaker_id may be null when unclear)"
        if speakers_block
        else "title/start/end/why_merged"
    )
    return (
        "You are the podcast AI drafting assistant for post-production review.\n"
        "Given transcript and candidate edit operations, propose review-safe suggestions only.\n\n"
        f"Return JSON object with keys: chapters, summary, show_notes, retake_decisions, operation_explanations.\n"
        f"- chapters: up to {max_chapters} items with {chapter_schema_hint}\n"
        "- summary: object with title, one_paragraph, key_points\n"
        "- show_notes: array of public-facing bullet strings\n"
        "- retake_decisions: array with operation_id, suggested_action, rationale, confidence, reasoning\n"
        "- operation_explanations: array with operation_id, why_risky, llm_reason, reasoning\n\n"
        "Use only provided operation ids.\n"
        "suggested_action must be one of {keep, probably_delete, manual_review}.\n\n"
        f"{speakers_block}"
        f"Transcript:\n{transcript or 'No transcript available'}\n\n"
        f"Operation candidates:\n{operation_context}"
    )


def _build_explain_prompt(operation_id: str, operation: dict[str, Any], transcript_excerpt: str) -> str:
    return (
        "You are a podcast editing auditor. Explain one operation clearly for a human reviewer.\n"
        "Respond with JSON object {\"operation_id\":..., \"risk\":..., \"rationale_score\":0-1, \"llm_reason\":...}.\n"
        f"Operation id: {operation_id}\n"
        f"Operation: {json.dumps(operation, ensure_ascii=False)}\n\n"
        "Short transcript context:\n"
        f"{transcript_excerpt or 'No transcript available'}"
    )


def _extract_json(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}\s*\Z", raw)
    if not match:
        raise AIServiceError("AI response was not JSON")
    return json.loads(match.group(0))


def chat_with_local_ai(
    *,
    base_url: str,
    model: str,
    payload: dict[str, Any],
    timeout_s: float = DEFAULT_TIMEOUT_SECONDS,
    api_key: str | None = None,
) -> str:
    request_payload = dict(payload)
    request_payload["model"] = model
    data = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = response.read().decode("utf-8")
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise AIServiceError(f"AI request failed: {exc}") from exc
    try:
        payload_json = json.loads(body)
    except json.JSONDecodeError as exc:
        raise AIServiceError(f"AI response invalid JSON: {exc}") from exc
    choices = payload_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIServiceError("AI response missing choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not content:
        raise AIServiceError("AI response missing message content")
    return str(content)


def _normalize_retake_decision(item: dict[str, Any], operation_ids: set[str]) -> dict[str, Any]:
    op_id = str(item.get("operation_id") or "")
    action = str(item.get("suggested_action") or "manual_review").strip() or "manual_review"
    if action not in {"keep", "probably_delete", "manual_review"}:
        action = "manual_review"
    return {
        "operation_id": op_id,
        "suggested_action": action,
        "rationale": str(item.get("rationale") or item.get("reason") or "")[:500],
        "confidence": _coerce_confidence(item.get("confidence")),
        "reasoning": str(item.get("reasoning") or ""),
        "operation_known": op_id in operation_ids,
    }


def _normalize_explanation(item: dict[str, Any], operation_ids: set[str]) -> dict[str, Any]:
    op_id = str(item.get("operation_id") or "")
    why_risky = str(item.get("why_risky") or item.get("risk") or "unknown")
    return {
        "operation_id": op_id,
        "risk": why_risky,
        "llm_reason": str(item.get("llm_reason") or item.get("reason") or ""),
        "reasoning": str(item.get("reasoning") or ""),
        "operation_known": op_id in operation_ids,
        "why_risky": why_risky,
    }


def _normalize_chapter(idx: int, chapter: dict[str, Any], *, attribution_enabled: bool = False) -> dict[str, Any]:
    start = chapter.get("start")
    end = chapter.get("end")
    try:
        start_value = float(start)
    except (TypeError, ValueError):
        start_value = 0.0
    try:
        end_value = float(end)
    except (TypeError, ValueError):
        end_value = 0.0
    out: dict[str, Any] = {
        "index": idx + 1,
        "title": str(chapter.get("title") or f"Chapter {idx + 1}").strip()[:180],
        "start": start_value,
        "end": end_value,
        "why_merged": str(chapter.get("why_merged") or chapter.get("reason") or "AI draft"),
    }
    if attribution_enabled:
        raw_speaker = chapter.get("speaker_id")
        if raw_speaker is None:
            speaker_id: str | None = None
        else:
            speaker_text = str(raw_speaker).strip()
            speaker_id = speaker_text or None
        out["speaker_id"] = speaker_id
    return out


def _normalize_summary(raw_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(raw_summary, dict):
        return {"title": "Episode summary", "one_paragraph": "", "key_points": []}
    return {
        "title": str(raw_summary.get("title") or "Episode summary"),
        "one_paragraph": str(raw_summary.get("one_paragraph") or ""),
        "key_points": [
            str(item).strip() for item in (raw_summary.get("key_points") or []) if str(item).strip()
        ],
    }


def _normalize_ai_draft_payload(
    raw: dict[str, Any],
    operation_ids: set[str],
    timeline_path: Path | None = None,
    *,
    attribution_enabled: bool = False,
) -> dict[str, Any]:
    chapters = [
        _normalize_chapter(idx, chapter, attribution_enabled=attribution_enabled)
        for idx, chapter in enumerate(raw.get("chapters") if isinstance(raw.get("chapters"), list) else [])
        if isinstance(chapter, dict)
    ]
    retake_raw = raw.get("retake_decisions") if isinstance(raw.get("retake_decisions"), list) else []
    explanations_raw = raw.get("operation_explanations") if isinstance(raw.get("operation_explanations"), list) else []
    show_notes = [
        str(note).strip()
        for note in (raw.get("show_notes") if isinstance(raw.get("show_notes"), list) else [])
        if str(note).strip()
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "chapters": chapters,
        "summary": _normalize_summary(raw.get("summary") if isinstance(raw.get("summary"), dict) else None),
        "show_notes": show_notes,
        "retake_decisions": [_normalize_retake_decision(item, operation_ids) for item in retake_raw if isinstance(item, dict)],
        "operation_explanations": [_normalize_explanation(item, operation_ids) for item in explanations_raw if isinstance(item, dict)],
        "metadata": {"source_timeline": str(timeline_path) if timeline_path else None},
    }


def generate_ai_draft(
    *,
    timeline: dict[str, Any] | None,
    transcript_segments: list[dict[str, Any]],
    base_url: str | None = None,
    model: str | None = None,
    timeout_s: float | None = None,
    max_chapters: int = 8,
    dry_prompt: bool = False,
    no_net: bool = False,
    api_key: str | None = None,
    timeline_path: str | Path | None = None,
    speaker_segments: list[dict[str, Any]] | None = None,
    speaker_labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not transcript_segments:
        raise ValueError("transcript segments are required for AI draft generation")

    base_url = base_url or _default_base_url()
    model = model or _default_model()
    timeout_s = _default_timeout() if timeout_s is None else timeout_s

    operations = timeline.get("operations") if isinstance(timeline, dict) else []
    candidates = [
        op
        for op in operations
        if op.get("type") in {"retake_cut", "speech_cut"} and op.get("operation_id")
    ]
    operation_ids = {str(op.get("operation_id")) for op in candidates}
    prompt = _build_draft_prompt(
        transcript_segments=transcript_segments,
        operation_payloads=_operation_payloads(candidates),
        max_chapters=max_chapters,
        speaker_segments=speaker_segments,
        speaker_labels=speaker_labels,
    )
    payload = _build_payload_json(model=model, prompt=prompt, max_tokens=900)
    distinct_speakers = {
        str(seg.get("speaker_id"))
        for seg in (speaker_segments or [])
        if seg.get("speaker_id")
    }
    attribution_enabled = bool(distinct_speakers)

    if dry_prompt or no_net:
        metadata: dict[str, Any] = {
            "source_timeline": str(timeline_path) if timeline_path else None,
        }
        if attribution_enabled:
            metadata["speaker_count"] = len(distinct_speakers)
            metadata["speaker_labels"] = dict(speaker_labels) if speaker_labels else None
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "dry_prompt": True,
            "model": model,
            "base_url": base_url,
            "max_chapters": max_chapters,
            "request": payload,
            "notes": "Dry prompt mode: payload was prepared but not executed.",
            "chapters": [],
            "summary": {"title": "", "one_paragraph": "", "key_points": []},
            "show_notes": [],
            "retake_decisions": [],
            "operation_explanations": [],
            "metadata": {
                **metadata,
                "source_segment_count": len(transcript_segments),
                "candidate_operation_count": len(candidates),
            },
        }

    content = chat_with_local_ai(
        base_url=base_url,
        model=model,
        payload=payload,
        timeout_s=timeout_s,
        api_key=api_key,
    )
    parsed = _extract_json(content)
    return _normalize_ai_draft_payload(parsed, operation_ids, Path(timeline_path) if timeline_path else None, attribution_enabled=attribution_enabled)


def build_ai_explanation(
    *,
    timeline: dict[str, Any],
    operation_id: str,
    transcript_segments: list[dict[str, Any]] | None = None,
    base_url: str | None = None,
    model: str | None = None,
    timeout_s: float | None = None,
    dry_prompt: bool = False,
    no_net: bool = False,
    api_key: str | None = None,
) -> dict[str, Any]:
    base_explanation = explain_operation(timeline, operation_id)
    base_url = base_url or _default_base_url()
    model = model or _default_model()
    prompt = _build_explain_prompt(
        operation_id=operation_id,
        operation=base_explanation,
        transcript_excerpt=_transcript_excerpt(transcript_segments or []),
    )
    ai_request = _build_payload_json(model=model, prompt=prompt, max_tokens=320)
    result = dict(base_explanation)
    result["schema_version"] = SCHEMA_VERSION
    result["operation_id"] = operation_id

    if dry_prompt or no_net:
        result["base_explanation"] = base_explanation
        result["ai_explanation"] = {
            "dry_prompt": True,
            "request": ai_request,
        }
        result["base_url"] = base_url
        result["model"] = model
        return result

    timeout_s = _default_timeout() if timeout_s is None else timeout_s
    content = chat_with_local_ai(
        base_url=base_url,
        model=model,
        payload=ai_request,
        timeout_s=timeout_s,
        api_key=api_key,
    )
    ai_payload = _extract_json(content)
    result["ai_explanation"] = {
        "risk": ai_payload.get("risk") or base_explanation.get("risk"),
        "rationale": str(ai_payload.get("rationale") or ai_payload.get("reason") or ""),
        "rationale_score": _coerce_confidence(ai_payload.get("rationale_score")),
        "llm_reason": str(ai_payload.get("llm_reason") or ai_payload.get("reason") or ""),
        "source": ai_payload,
    }
    result["ai_request_model"] = model
    result["ai_request_base_url"] = base_url
    result["base_explanation"] = base_explanation
    return result
