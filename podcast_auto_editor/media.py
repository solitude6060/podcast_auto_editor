from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import AppConfig
from .timeline import sha256_file

_SILENCE_START = re.compile(r"silence_start: (?P<value>[0-9.]+)")
_SILENCE_END = re.compile(r"silence_end: (?P<end>[0-9.]+) \| silence_duration: (?P<duration>[0-9.]+)")
_LOUDNORM_JSON = re.compile(r"\{\s*\"input_i\".*?\}\s*", re.DOTALL)


class MediaToolError(RuntimeError):
    pass


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise MediaToolError(f"required tool not found on PATH: {name}")
    return path


def run_command(command: list[str], text: bool = True):
    return subprocess.run(command, text=text, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def ffprobe(path: str | Path) -> dict[str, Any]:
    require_tool("ffprobe")
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    result = run_command(command)
    if result.returncode != 0:
        raise MediaToolError(result.stderr.strip() or "ffprobe failed")
    return json.loads(result.stdout)


def probe_media(path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = Path(path)
    data = ffprobe(path)
    fmt = data.get("format", {})
    duration = float(fmt.get("duration") or 0.0)
    manifest = {
        "path": str(path),
        "sha256": sha256_file(path) if path.exists() else None,
        "duration": duration,
        "format": fmt.get("format_name"),
        "size": int(fmt.get("size", 0) or 0),
    }
    tracks = []
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "audio":
            tracks.append(
                {
                    "track_id": f"audio:{stream.get('index', 0)}",
                    "type": "audio",
                    "codec": stream.get("codec_name"),
                    "sample_rate": int(stream.get("sample_rate") or 48000),
                    "channels": int(stream.get("channels") or 1),
                    "duration": float(stream["duration"]) if stream.get("duration") is not None else None,
                }
            )
        elif stream.get("codec_type") == "video":
            tracks.append(
                {
                    "track_id": f"video:{stream.get('index', 0)}",
                    "type": "video",
                    "codec": stream.get("codec_name"),
                    "duration": float(stream["duration"]) if stream.get("duration") is not None else None,
                    "timebase": stream.get("time_base", "1/90000"),
                    "start_pts": int(stream.get("start_pts") or 0),
                    "avg_frame_rate": stream.get("avg_frame_rate"),
                }
            )
    return manifest, tracks


def detect_silence(path: str | Path, config: AppConfig) -> list[dict[str, float]]:
    require_tool("ffmpeg")
    q = config.quality
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-af",
        f"silencedetect=noise={q.silence_threshold_dbfs}dB:d={q.min_silence_duration_s}",
        "-f",
        "null",
        "-",
    ]
    result = run_command(command)
    if result.returncode != 0 and "silence_" not in result.stderr:
        raise MediaToolError(result.stderr.strip() or "ffmpeg silencedetect failed")
    starts: list[float] = []
    segments: list[dict[str, float]] = []
    for line in result.stderr.splitlines():
        start_match = _SILENCE_START.search(line)
        if start_match:
            starts.append(float(start_match.group("value")))
        end_match = _SILENCE_END.search(line)
        if end_match:
            start = starts.pop(0) if starts else float(end_match.group("end")) - float(end_match.group("duration"))
            end = float(end_match.group("end"))
            segments.append({"start": start, "end": end, "duration": end - start})
    return segments



def measure_audio_quality(path: str | Path) -> dict[str, Any]:
    require_tool("ffmpeg")
    command = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", "loudnorm=print_format=json", "-f", "null", "-",
    ]
    result = run_command(command)
    match = _LOUDNORM_JSON.search(result.stderr)
    if result.returncode != 0 or not match:
        raise MediaToolError(result.stderr.strip() or "ffmpeg loudnorm analysis failed")
    data = json.loads(match.group(0))

    # Measure hard clipping by decoding signed 16-bit PCM and counting samples at full scale.
    pcm = run_command(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-f", "s16le", "-acodec", "pcm_s16le", "-"], text=False)
    if pcm.returncode != 0:
        stderr = pcm.stderr.decode(errors="replace") if isinstance(pcm.stderr, bytes) else pcm.stderr
        raise MediaToolError(stderr.strip() or "ffmpeg PCM decode failed for clipping analysis")
    raw = pcm.stdout
    clipped = 0
    for i in range(0, len(raw) - 1, 2):
        sample = int.from_bytes(raw[i:i+2], "little", signed=True)
        if sample in (-32768, 32767):
            clipped += 1
    return {
        "integrated_lufs": float(data["input_i"]),
        "true_peak_db": float(data["input_tp"]),
        "clipped_samples": clipped,
    }


def measure_av_sync(path: str | Path) -> dict[str, Any]:
    manifest, tracks = probe_media(path)
    audio = next((track for track in tracks if track.get("type") == "audio"), None)
    video = next((track for track in tracks if track.get("type") == "video"), None)
    if not audio or not video:
        return {"passed": False, "drift_s": None, "tolerance_s": 0.100, "method": "ffprobe-duration-start-delta", "reason": "missing audio or video stream"}
    if audio.get("duration") is None or video.get("duration") is None:
        return {"passed": False, "drift_s": None, "tolerance_s": 0.100, "method": "ffprobe-audio-video-duration-delta", "reason": "unmeasured stream duration"}
    audio_duration = float(audio["duration"])
    video_duration = float(video["duration"])
    duration_drift = abs(audio_duration - video_duration)
    return {
        "passed": duration_drift <= 0.100,
        "drift_s": duration_drift,
        "tolerance_s": 0.100,
        "method": "ffprobe-audio-video-duration-delta",
    }

def render_audio(input_path: str | Path, output_path: str | Path, kept: list[dict[str, float]], config: AppConfig, channels: int = 2) -> None:
    require_tool("ffmpeg")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not kept:
        raise MediaToolError("cannot render with no kept segments")
    select_expr = "+".join(f"between(t,{seg['source_start']:.6f},{seg['source_end']:.6f})" for seg in kept)
    target = config.quality.mono_loudness_lufs if channels == 1 else config.quality.stereo_loudness_lufs
    filters = f"aselect='{select_expr}',asetpts=N/SR/TB,loudnorm=I={target}:TP={config.quality.true_peak_ceiling_db}:LRA=11"
    command = ["ffmpeg", "-y", "-hide_banner", "-i", str(input_path), "-af", filters, str(output_path)]
    result = run_command(command)
    if result.returncode != 0:
        raise MediaToolError(result.stderr.strip() or "ffmpeg audio render failed")


def render_video(input_path: str | Path, output_path: str | Path, kept: list[dict[str, float]]) -> None:
    require_tool("ffmpeg")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not kept:
        raise MediaToolError("cannot render with no kept segments")
    select_expr = "+".join(f"between(t,{seg['source_start']:.6f},{seg['source_end']:.6f})" for seg in kept)
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-i",
        str(input_path),
        "-vf",
        f"select='{select_expr}',setpts=N/FRAME_RATE/TB",
        "-af",
        f"aselect='{select_expr}',asetpts=N/SR/TB",
        str(output_path),
    ]
    result = run_command(command)
    if result.returncode != 0:
        raise MediaToolError(result.stderr.strip() or "ffmpeg video render failed")
