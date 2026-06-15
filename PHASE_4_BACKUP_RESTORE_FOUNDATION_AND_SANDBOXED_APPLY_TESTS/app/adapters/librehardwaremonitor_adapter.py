from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.command_runner import SafeCommandRunner


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

    def sensor_snapshot(self) -> dict[str, Any]:
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
            parsed = self._read_with_dll(script, dll)
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

    def _read_with_dll(self, script: Path, dll: str) -> dict[str, Any]:
        result = self.runner.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-DllPath", dll],
            timeout=18,
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

    def headline(self, snapshot: dict[str, Any] | None = None) -> dict[str, str]:
        data = snapshot or self.sensor_snapshot()
        if not data.get("ok"):
            return {"CPU": "LHM unavailable", "Fan": "Fan n/a", "Sensors": data.get("error", "No readings")}
        sensors = data.get("sensors", [])
        cpu_temp = self._first_sensor(sensors, "Temperature", ["cpu", "package", "tdie", "tctl"])
        fan = self._first_sensor(sensors, "Fan", [])
        return {
            "CPU": f"{cpu_temp:.0f} C" if cpu_temp is not None else "CPU temp n/a",
            "Fan": f"{fan:.0f} RPM" if fan is not None else "Fan n/a",
            "Sensors": f"{len(sensors)} readings",
        }

    def _first_sensor(self, sensors: list[dict[str, Any]], sensor_type: str, keywords: list[str]) -> float | None:
        for row in sensors:
            if row.get("sensor_type") != sensor_type:
                continue
            name = " ".join([str(row.get("hardware", "")), str(row.get("name", ""))]).lower()
            if keywords and not any(key in name for key in keywords):
                continue
            try:
                value = float(row.get("value"))
                if sensor_type in {"Temperature", "Fan"} and value <= 1:
                    continue
                return value
            except (TypeError, ValueError):
                return None
        return None
