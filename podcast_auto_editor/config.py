from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class QualityConfig:
    stereo_loudness_lufs: float = -16.0
    mono_loudness_lufs: float = -19.0
    loudness_tolerance_lu: float = 1.0
    true_peak_ceiling_db: float = -1.0
    silence_threshold_dbfs: float = -40.0
    min_silence_duration_s: float = 1.5
    speech_padding_s: float = 0.25
    max_clipped_samples: int = 0
    av_sync_tolerance_s: float = 0.100
    subtitle_tolerance_s: float = 0.250


@dataclass(frozen=True)
class RetakeConfig:
    auto_low_risk_speech: bool = False
    auto_accept_confidence: float = 0.90
    duplicate_window_s: float = 20.0
    marker_phrases: tuple[str, ...] = (
        "start again",
        "let me say that again",
        "say that again",
        "redo that",
        "take two",
    )


@dataclass(frozen=True)
class AppConfig:
    quality: QualityConfig = field(default_factory=QualityConfig)
    retake: RetakeConfig = field(default_factory=RetakeConfig)
    output_audio_ext: str = "wav"
    publish_audio_ext: str = "mp3"


def _merge_dataclass(default_obj: Any, overrides: dict[str, Any]) -> Any:
    values = asdict(default_obj)
    for key, value in overrides.items():
        if key in values:
            values[key] = value
    return type(default_obj)(**values)


def load_config(path: str | Path | None = None) -> AppConfig:
    """Load JSON config, merging partial overrides onto safe MVP defaults."""
    default = AppConfig()
    if path is None:
        return default
    data = json.loads(Path(path).read_text())
    quality = _merge_dataclass(default.quality, data.get("quality", {}))
    retake = _merge_dataclass(default.retake, data.get("retake", {}))
    output_audio_ext = data.get("output_audio_ext", default.output_audio_ext)
    publish_audio_ext = data.get("publish_audio_ext", default.publish_audio_ext)
    return AppConfig(
        quality=quality,
        retake=retake,
        output_audio_ext=output_audio_ext,
        publish_audio_ext=publish_audio_ext,
    )


def config_to_dict(config: AppConfig) -> dict[str, Any]:
    return asdict(config)
