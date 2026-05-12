from __future__ import annotations

from typing import Any

from .config import QualityConfig


def target_loudness(channels: int, quality: QualityConfig) -> float:
    return quality.mono_loudness_lufs if channels == 1 else quality.stereo_loudness_lufs


def evaluate_quality(metrics: dict[str, Any], channels: int, quality: QualityConfig) -> dict[str, Any]:
    target = target_loudness(channels, quality)
    loudness = metrics.get("integrated_lufs")
    true_peak = metrics.get("true_peak_db")
    clipped_value = metrics.get("clipped_samples")
    clipped = int(clipped_value) if clipped_value is not None else None
    checks = []
    checks.append({
        "name": "loudness",
        "passed": loudness is not None and abs(float(loudness) - target) <= quality.loudness_tolerance_lu,
        "target": target,
        "actual": loudness,
    })
    checks.append({
        "name": "true_peak",
        "passed": true_peak is not None and float(true_peak) <= quality.true_peak_ceiling_db,
        "target": quality.true_peak_ceiling_db,
        "actual": true_peak,
    })
    checks.append({"name": "clipped_samples", "passed": clipped is not None and clipped <= quality.max_clipped_samples, "target": quality.max_clipped_samples, "actual": clipped})
    return {"passed": all(check["passed"] for check in checks), "checks": checks, "target_loudness_lufs": target}
