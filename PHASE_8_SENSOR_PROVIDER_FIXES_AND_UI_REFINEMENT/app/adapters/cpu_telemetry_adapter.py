from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.command_runner import SafeCommandRunner


class CpuTelemetryAdapter:
    """Read-only CPU provider discovery for Phase 8 telemetry diagnostics."""

    def __init__(self, runner: SafeCommandRunner, phase1_lhm: dict[str, Any] | None = None, phase_root: Path | None = None) -> None:
        self.runner = runner
        self.phase1_lhm = phase1_lhm or {}
        self.phase_root = phase_root

    def provider_status(self, normalized_model: dict[str, Any] | None = None, probe_external: bool = False) -> dict[str, Any]:
        cpu_provider = ((normalized_model or {}).get("diagnostics", {}) or {}).get("cpu_provider", {}) or {}
        return {
            "librehardwaremonitor": self._lhm_status(cpu_provider),
            "windows_counters": self._windows_counter_status() if probe_external else self._not_probed("available if counters respond"),
            "acpi_thermal_zone": self._acpi_status() if probe_external else self._not_probed("diagnostic only; not probed during UI render"),
            "hwinfo": self._hwinfo_status() if probe_external else self._not_probed("optional provider; not probed during UI render"),
        }

    def _not_probed(self, notes: str) -> dict[str, Any]:
        return {"status": "not probed", "notes": notes}

    def _lhm_status(self, cpu_provider: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": cpu_provider.get("status") or ("available" if self.phase1_lhm.get("found") else "unavailable"),
            "sensor_count": cpu_provider.get("sensor_count"),
            "cpu_load_valid": bool(cpu_provider.get("cpu_load_valid")),
            "cpu_temp_valid": bool(cpu_provider.get("cpu_temp_valid")),
            "cpu_power_valid": bool(cpu_provider.get("cpu_power_valid")),
            "cpu_clock_valid": bool(cpu_provider.get("cpu_clock_valid")),
            "cpu_voltage_valid": bool(cpu_provider.get("cpu_voltage_valid")),
            "summary": cpu_provider.get("summary") or "LibreHardwareMonitor provider status is based on the current normalized model.",
        }

    def _windows_counter_status(self) -> dict[str, Any]:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-Counter '\\Processor Information(_Total)\\% Processor Utility' -SampleInterval 1 -MaxSamples 1 | ConvertTo-Json -Depth 6",
        ]
        try:
            result = self.runner.run(command, timeout=6, read_only=True)
        except Exception as exc:
            return {"status": "unavailable", "error": str(exc)}
        return {
            "status": "available" if result.exit_code == 0 else "unavailable",
            "exit_code": result.exit_code,
            "error": result.stderr or result.error,
            "notes": "Read-only Windows performance counter probe.",
        }

    def _acpi_status(self) -> dict[str, Any]:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -First 1 | ConvertTo-Json -Depth 4",
        ]
        try:
            result = self.runner.run(command, timeout=6, read_only=True)
        except Exception as exc:
            return {"status": "unavailable", "diagnostic_only": True, "error": str(exc)}
        available = result.exit_code == 0 and bool((result.stdout or "").strip())
        return {
            "status": "diagnostic_only" if available else "unavailable",
            "diagnostic_only": True,
            "exit_code": result.exit_code,
            "error": result.stderr or result.error,
            "notes": "ACPI thermal zones are not treated as CPU package temperature unless manually verified.",
        }

    def _hwinfo_status(self) -> dict[str, Any]:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-Process -Name HWiNFO64,HWiNFO32 -ErrorAction SilentlyContinue | Select-Object ProcessName,Id,Path | ConvertTo-Json -Depth 4",
        ]
        try:
            result = self.runner.run(command, timeout=5, read_only=True)
        except Exception as exc:
            return {"status": "not detected", "shared_memory": "unknown", "error": str(exc)}
        detected = result.exit_code == 0 and bool((result.stdout or "").strip())
        return {
            "status": "detected" if detected else "not detected",
            "shared_memory": "unknown",
            "exit_code": result.exit_code,
            "error": result.stderr or result.error,
            "notes": "Phase 8 does not modify HWiNFO settings; shared memory remains a future optional provider.",
        }
