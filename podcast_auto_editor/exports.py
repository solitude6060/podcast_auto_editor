from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .artifacts import RunPaths


@dataclass(frozen=True)
class ExportProfile:
    name: str
    container: str
    channels: int | None
    compatibility_default: bool = False


EXPORT_PROFILES: dict[str, ExportProfile] = {
    "archive-wav": ExportProfile(name="archive-wav", container="wav", channels=None, compatibility_default=True),
    "podcast-stereo": ExportProfile(name="podcast-stereo", container="mp3", channels=2),
    "podcast-mono": ExportProfile(name="podcast-mono", container="mp3", channels=1),
}


def default_export_profiles() -> list[ExportProfile]:
    return [EXPORT_PROFILES["archive-wav"], EXPORT_PROFILES["podcast-stereo"], EXPORT_PROFILES["podcast-mono"]]


def export_output_path(paths: RunPaths, profile: ExportProfile) -> Path:
    if profile.compatibility_default:
        return paths.edited_wav
    return paths.exports / f"episode.{profile.name}.{profile.container}"
