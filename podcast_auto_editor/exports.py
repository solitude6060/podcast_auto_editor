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


def select_export_profiles(profile_names: list[str] | tuple[str, ...] | None = None) -> list[ExportProfile]:
    if profile_names is None:
        return default_export_profiles()
    if not profile_names:
        raise ValueError("export_profiles must contain at least one profile")
    selected = []
    for name in profile_names:
        try:
            selected.append(EXPORT_PROFILES[name])
        except KeyError as exc:
            raise ValueError(f"unknown export profile: {name}") from exc
    return selected


def export_output_path(paths: RunPaths, profile: ExportProfile) -> Path:
    if profile.compatibility_default:
        return paths.edited_wav
    return paths.exports / f"episode.{profile.name}.{profile.container}"
