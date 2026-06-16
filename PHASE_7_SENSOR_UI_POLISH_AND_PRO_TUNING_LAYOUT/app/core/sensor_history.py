from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any


class SensorHistory:
    """Small in-memory rolling telemetry history for lightweight charts."""

    TRACKED_KEYS = [
        "cpu_temp_c",
        "cpu_load_percent",
        "cpu_power_w",
        "gpu_temp_c",
        "gpu_util_percent",
        "gpu_power_w",
        "gpu_clock_mhz",
        "vram_used_mb",
        "fps",
        "frame_time_ms",
        "ram_load_percent",
        "fan_rpm",
    ]

    def __init__(self, max_samples: int = 120) -> None:
        self.max_samples = max_samples
        self.samples: dict[str, deque[tuple[str, float]]] = {key: deque(maxlen=max_samples) for key in self.TRACKED_KEYS}

    def add_model(self, model: dict[str, Any]) -> None:
        headline = model.get("headline", {})
        timestamp = model.get("generated_local") or datetime.now().isoformat(timespec="seconds")
        for key in self.TRACKED_KEYS:
            value = self._number(headline.get(key))
            if value is not None:
                self.samples[key].append((timestamp, value))

    def values(self, key: str) -> list[float]:
        return [value for _timestamp, value in self.samples.get(key, [])]

    def snapshot(self) -> dict[str, list[dict[str, float | str]]]:
        return {
            key: [{"timestamp": timestamp, "value": value} for timestamp, value in rows]
            for key, rows in self.samples.items()
            if rows
        }

    def _number(self, value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
