from __future__ import annotations

from typing import Any


def format_srt_time(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_vtt_time(seconds: float) -> str:
    return format_srt_time(seconds).replace(",", ".")


def validate_cues(cues: list[dict[str, Any]], duration: float, tolerance_s: float = 0.250) -> list[str]:
    errors: list[str] = []
    last_start = -1.0
    last_end = 0.0
    for idx, cue in enumerate(cues):
        start = float(cue.get("start", -1))
        end = float(cue.get("end", -1))
        if start < -tolerance_s:
            errors.append(f"cue[{idx}] starts before 0")
        if end < start:
            errors.append(f"cue[{idx}] end before start")
        if start < last_start:
            errors.append(f"cue[{idx}] start is not monotonic")
        if start < last_end - tolerance_s:
            errors.append(f"cue[{idx}] overlaps previous cue")
        if end > duration + tolerance_s:
            errors.append(f"cue[{idx}] ends after duration")
        last_start = start
        last_end = max(last_end, end)
    return errors


def cues_to_srt(cues: list[dict[str, Any]]) -> str:
    blocks = []
    for idx, cue in enumerate(cues, 1):
        blocks.append(f"{idx}\n{format_srt_time(float(cue['start']))} --> {format_srt_time(float(cue['end']))}\n{cue.get('text', '')}")
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def cues_to_vtt(cues: list[dict[str, Any]]) -> str:
    blocks = ["WEBVTT", ""]
    for cue in cues:
        blocks.append(f"{format_vtt_time(float(cue['start']))} --> {format_vtt_time(float(cue['end']))}\n{cue.get('text', '')}\n")
    return "\n".join(blocks).rstrip() + "\n"


def heuristic_chapters(cues: list[dict[str, Any]], duration: float, min_chapter_s: float = 300.0) -> list[dict[str, Any]]:
    if not cues:
        return [{"title": "Episode", "start": 0.0, "end": duration, "provenance": "heuristic-empty-transcript"}]
    chapters = [{"title": "Opening", "start": 0.0, "provenance": "heuristic-transcript"}]
    next_boundary = min_chapter_s
    chapter_num = 2
    for cue in cues:
        start = float(cue.get("start", 0.0))
        if start >= next_boundary and duration - start >= min(60.0, min_chapter_s / 2):
            chapters.append({"title": f"Chapter {chapter_num}", "start": start, "provenance": "heuristic-transcript"})
            chapter_num += 1
            next_boundary = start + min_chapter_s
    for idx, chapter in enumerate(chapters):
        chapter["end"] = chapters[idx + 1]["start"] if idx + 1 < len(chapters) else duration
    return chapters


def validate_chapters(chapters: list[dict[str, Any]], duration: float) -> list[str]:
    errors: list[str] = []
    last = -1.0
    for idx, chapter in enumerate(chapters):
        start = float(chapter.get("start", -1))
        end = float(chapter.get("end", duration))
        if not str(chapter.get("title", "")).strip():
            errors.append(f"chapter[{idx}] missing title")
        if start < 0 or end > duration + 1e-6:
            errors.append(f"chapter[{idx}] out of bounds")
        if start < last:
            errors.append(f"chapter[{idx}] not monotonic")
        if end < start:
            errors.append(f"chapter[{idx}] end before start")
        if "heuristic" not in str(chapter.get("provenance", "")):
            errors.append(f"chapter[{idx}] missing heuristic provenance")
        last = start
    return errors
