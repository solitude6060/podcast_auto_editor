from __future__ import annotations

from pathlib import Path

from .media import MediaToolError, require_tool, run_command


def make_silence_fixture(path: str | Path) -> Path:
    """Create a deterministic 3-part audio demo fixture with ffmpeg when available."""
    require_tool("ffmpeg")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    result = run_command(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=1",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=mono:d=2",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=1",
            "-filter_complex",
            "[0:a][1:a][2:a]concat=n=3:v=0:a=1",
            str(path),
        ]
    )
    if result.returncode != 0:
        raise MediaToolError(result.stderr.strip() or "failed to create silence fixture")
    return path


def make_mp4_fixture(path: str | Path) -> Path:
    """Create a deterministic one-second audio/video demo fixture with ffmpeg when available."""
    require_tool("ffmpeg")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    result = run_command(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=64x64:rate=25:duration=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            "-shortest",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ]
    )
    if result.returncode != 0:
        raise MediaToolError(result.stderr.strip() or "failed to create mp4 fixture")
    return path


def make_demo_fixtures(output_dir: str | Path) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return {
        "audio": make_silence_fixture(output_dir / "demo-silence.wav"),
        "video": make_mp4_fixture(output_dir / "demo-av.mp4"),
    }
