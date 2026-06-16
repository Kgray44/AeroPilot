from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.command_runner import SafeCommandRunner
from app.core.sensor_normalizer import SensorNormalizer


class LibreHardwareMonitorAdapter:
    def __init__(self, phase1_lhm: dict[str, Any], runner: SafeCommandRunner | None = None, phase_root: Path | None = None) -> None:
        self.phase1 = phase1_lhm
        self.runner = runner
        self.phase_root = phase_root

    def status(self) -> dict[str, Any]:
        return {
            "found": bool(self.phase1.get("found")),
            "primary_executable_path": self.phase1.get("primary_executable_path"),
            "primary_library_path": self.primary_library_path(),
            "library_paths": self.phase1.get("library_paths", []),
            "actual_read_supported": bool(self.runner and self.phase_root and self.primary_library_path()),
            "notes": "AeroTune reads LibreHardwareMonitor sensors through a local read-only PowerShell probe when the DLL loads successfully.",
        }

    def primary_library_path(self) -> str | None:
        primary = self.phase1.get("primary_library_path")
        if primary and Path(primary).exists():
            return primary
        for row in self.phase1.get("library_paths", []):
            path = row.get("path") if isinstance(row, dict) else str(row)
            if path and Path(path).exists():
                return path
        return primary

    def sensor_snapshot(self, samples: int = 3, sample_delay_ms: int = 500) -> dict[str, Any]:
        if not self.runner or not self.phase_root:
            return {"ok": False, "source": "adapter", "error": "LibreHardwareMonitor runner/root not configured.", "sensors": []}
        dlls = self.library_paths()
        if not dlls:
            return {"ok": False, "source": "phase1", "error": "LibreHardwareMonitorLib.dll was not discovered.", "sensors": []}
        script = self.phase_root / "scripts" / "read_librehardwaremonitor_sensors.ps1"
        if not script.exists():
            return {"ok": False, "source": "app", "error": f"Sensor probe script missing: {script}", "sensors": []}
        failures = []
        for dll in dlls:
            parsed = self._read_with_dll(script, dll, samples=samples, sample_delay_ms=sample_delay_ms)
            if parsed.get("ok"):
                return parsed
            failures.append({"dll_path": dll, "error": parsed.get("error")})
        return {"ok": False, "source": "librehardwaremonitor", "error": "All discovered LibreHardwareMonitor DLL probes failed.", "failures": failures, "sensors": []}

    def library_paths(self) -> list[str]:
        paths: list[str] = []
        primary = self.primary_library_path()
        if primary:
            paths.append(primary)
        for row in self.phase1.get("library_paths", []):
            path = row.get("path") if isinstance(row, dict) else str(row)
            if path and Path(path).exists() and path not in paths:
                paths.append(path)
        return paths

    def _read_with_dll(self, script: Path, dll: str, samples: int = 3, sample_delay_ms: int = 500) -> dict[str, Any]:
        result = self.runner.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                "-DllPath",
                dll,
                "-Samples",
                str(max(1, int(samples))),
                "-SampleDelayMs",
                str(max(0, int(sample_delay_ms))),
            ],
            timeout=24,
            read_only=True,
        )
        if result.exit_code not in (0, None) and not result.stdout:
            return {"ok": False, "source": "librehardwaremonitor", "error": result.stderr or result.error, "command": result.to_dict(), "sensors": []}
        try:
            parsed = json.loads(result.stdout)
        except Exception as exc:
            return {"ok": False, "source": "librehardwaremonitor", "error": f"Could not parse sensor JSON: {exc}", "command": result.to_dict(), "sensors": []}
        parsed["source"] = "librehardwaremonitor"
        parsed["command"] = result.to_dict()
        return parsed

    def headline(self, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        data = snapshot or self.sensor_snapshot()
        model = SensorNormalizer().normalize(lhm_snapshot=data, nvidia_snapshot={"ok": False}, presentmon_snapshot={"ok": False})
        headline = dict(model.get("headline", {}))
        headline["diagnostics"] = model.get("diagnostics", {}).get("cpu_temperature", {})
        if headline:
            return headline
        if not data.get("ok"):
            return {
                "ok": False,
                "cpu_temp_c": None,
                "cpu_temp_name": None,
                "cpu_temp_display": "CPU temp unavailable",
                "cpu_load_percent": None,
                "cpu_load_display": None,
                "cpu_power_w": None,
                "cpu_power_display": None,
                "fan_rpm": None,
                "fan_display": "Fan unavailable",
                "sensor_count": 0,
                "sensors_display": data.get("error", "No readings"),
                "status_display": "CPU telemetry unavailable",
                "error": data.get("error", "No readings"),
            }
        sensors = data.get("sensors", [])
        cpu_temp_sensor = self._best_cpu_temperature_sensor(sensors)
        cpu_load_sensor = self._best_cpu_load_sensor(sensors)
        cpu_power_sensor = self._best_cpu_power_sensor(sensors)
        fan_sensor = self._first_sensor_row(sensors, "Fan", [])
        cpu_temp = self._sensor_float(cpu_temp_sensor)
        cpu_load = self._sensor_float(cpu_load_sensor)
        cpu_power = self._sensor_float(cpu_power_sensor)
        fan = self._sensor_float(fan_sensor)
        temp_display = self._cpu_temperature_display(cpu_temp_sensor, cpu_temp)
        load_display = f"Load {cpu_load:.0f}%" if cpu_load is not None else None
        power_display = f"CPU power {cpu_power:.1f} W" if cpu_power is not None else None
        fan_display = f"Fan {fan:.0f} RPM" if fan is not None else "Fan unavailable"
        sensors_display = f"{len(sensors)} readings"
        parts = [f"CPU {temp_display}" if cpu_temp is not None else "CPU temp unavailable"]
        if load_display:
            parts.append(load_display)
        parts.append(fan_display)
        parts.append(sensors_display)
        return {
            "ok": True,
            "CPU": temp_display if cpu_temp is not None else "temp unavailable",
            "Fan": fan_display,
            "Sensors": sensors_display,
            "cpu_temp_c": cpu_temp,
            "cpu_temp_name": cpu_temp_sensor.get("name") if cpu_temp_sensor else None,
            "cpu_temp_hardware": cpu_temp_sensor.get("hardware") if cpu_temp_sensor else None,
            "cpu_temp_display": temp_display,
            "cpu_load_percent": cpu_load,
            "cpu_load_name": cpu_load_sensor.get("name") if cpu_load_sensor else None,
            "cpu_load_display": load_display,
            "cpu_power_w": cpu_power,
            "cpu_power_name": cpu_power_sensor.get("name") if cpu_power_sensor else None,
            "cpu_power_display": power_display,
            "fan_rpm": fan,
            "fan_name": fan_sensor.get("name") if fan_sensor else None,
            "fan_display": fan_display,
            "sensor_count": len(sensors),
            "sensors_display": sensors_display,
            "status_display": " | ".join(parts),
        }

    def _first_sensor_row(self, sensors: list[dict[str, Any]], sensor_type: str, keywords: list[str]) -> dict[str, Any] | None:
        for row in sensors:
            if str(row.get("sensor_type", "")).lower() != sensor_type.lower():
                continue
            name = " ".join([str(row.get("hardware", "")), str(row.get("name", ""))]).lower()
            if keywords and not any(key in name for key in keywords):
                continue
            value = self._sensor_float(row)
            if value is None:
                continue
            if sensor_type.lower() == "temperature" and not self._valid_temperature(value):
                continue
            if sensor_type.lower() == "fan" and value <= 1:
                continue
            return row
        return None

    def _best_cpu_temperature_sensor(self, sensors: list[dict[str, Any]]) -> dict[str, Any] | None:
        candidates = []
        for row in sensors:
            if str(row.get("sensor_type", "")).lower() != "temperature":
                continue
            if str(row.get("hardware_type", "")).lower() != "cpu":
                continue
            value = self._sensor_float(row)
            if value is None or not self._valid_temperature(value):
                continue
            rank = self._cpu_temperature_rank(row)
            candidates.append((rank, -value, row))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][2]

    def _cpu_temperature_rank(self, row: dict[str, Any]) -> int:
        text = " ".join([str(row.get("hardware", "")), str(row.get("name", ""))]).lower()
        priorities = [
            ("cpu package", 0),
            ("package", 1),
            ("core max", 2),
            ("max", 3),
            ("average", 4),
            ("cpu", 5),
            ("core", 6),
            ("tdie", 7),
            ("tctl", 8),
        ]
        for keyword, rank in priorities:
            if keyword in text:
                return rank
        return 100

    def _best_cpu_load_sensor(self, sensors: list[dict[str, Any]]) -> dict[str, Any] | None:
        return self._best_cpu_metric_sensor(sensors, "Load", ["total", "cpu total", "cpu", "package"])

    def _best_cpu_power_sensor(self, sensors: list[dict[str, Any]]) -> dict[str, Any] | None:
        return self._best_cpu_metric_sensor(sensors, "Power", ["package", "cpu package", "cpu", "core"])

    def _best_cpu_metric_sensor(self, sensors: list[dict[str, Any]], sensor_type: str, keywords: list[str]) -> dict[str, Any] | None:
        candidates = []
        for row in sensors:
            if str(row.get("sensor_type", "")).lower() != sensor_type.lower():
                continue
            if str(row.get("hardware_type", "")).lower() != "cpu":
                continue
            value = self._sensor_float(row)
            if value is None or value < 0:
                continue
            text = " ".join([str(row.get("hardware", "")), str(row.get("name", ""))]).lower()
            rank = next((idx for idx, keyword in enumerate(keywords) if keyword in text), 100)
            candidates.append((rank, -value, row))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][2]

    def _sensor_float(self, row: dict[str, Any] | None) -> float | None:
        if not row:
            return None
        try:
            return float(row.get("value"))
        except (TypeError, ValueError):
            return None

    def _valid_temperature(self, value: float) -> bool:
        return 1 < value < 125

    def _cpu_temperature_display(self, row: dict[str, Any] | None, value: float | None) -> str:
        if value is None:
            return "temp unavailable"
        suffix = ""
        if row:
            name = str(row.get("name") or "").strip()
            suffix = self._clean_temperature_suffix(name)
        if suffix:
            return f"{value:.0f} C {suffix}"
        return f"{value:.0f} C"

    def _clean_temperature_suffix(self, name: str) -> str:
        cleaned = name.replace("#", "").strip()
        lowered = cleaned.lower()
        replacements = [
            ("cpu package", "Package"),
            ("package", "Package"),
            ("core max", "Core Max"),
            ("max", "Max"),
            ("average", "Average"),
            ("tdie", "Tdie"),
            ("tctl", "Tctl"),
        ]
        for needle, label in replacements:
            if needle in lowered:
                return label
        if lowered.startswith("cpu "):
            cleaned = cleaned[4:].strip()
        if lowered in ("cpu", "temperature"):
            return ""
        return cleaned
