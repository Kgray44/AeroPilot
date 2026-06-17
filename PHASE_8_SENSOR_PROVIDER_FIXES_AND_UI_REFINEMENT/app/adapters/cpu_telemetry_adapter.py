from __future__ import annotations

import ctypes
import json
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
        provider_statuses = ((normalized_model or {}).get("diagnostics", {}) or {}).get("provider_statuses", {}) or {}
        if provider_statuses:
            return {
                "librehardwaremonitor": provider_statuses.get("librehardwaremonitor", {}),
                "windows_counters": provider_statuses.get("windows_counters", {}),
                "wmi_cim_thermal": provider_statuses.get("wmi_cim_thermal", {}),
                "acpi_thermal_zone": provider_statuses.get("acpi_thermal", provider_statuses.get("acpi_thermal_zone", {})),
                "hwinfo": provider_statuses.get("hwinfo", {}),
            }
        cpu_provider = ((normalized_model or {}).get("diagnostics", {}) or {}).get("cpu_provider", {}) or {}
        return {
            "librehardwaremonitor": self._lhm_status(cpu_provider),
            "windows_counters": self._windows_counter_status() if probe_external else self._not_probed("available if counters respond"),
            "wmi_cim_thermal": self._wmi_cim_status() if probe_external else self._not_probed("diagnostic only; not probed during UI render"),
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
        snapshot = self.windows_counter_snapshot()
        return {
            "status": snapshot.get("status"),
            "sensor_count": len(snapshot.get("sensors", [])),
            "error": snapshot.get("error"),
            "notes": snapshot.get("notes"),
        }

    def windows_counter_snapshot(self) -> dict[str, Any]:
        script = r"""
$ErrorActionPreference = 'Stop'
$wanted = @(
  '\Processor Information(_Total)\% Processor Utility',
  '\Processor Information(_Total)\Processor Frequency',
  '\Processor Information(_Total)\% Processor Performance',
  '\Processor Information(*)\% Processor Utility'
)
$samples = @()
foreach ($path in $wanted) {
  try {
    $counter = Get-Counter $path -SampleInterval 1 -MaxSamples 1 -ErrorAction Stop
    foreach ($sample in $counter.CounterSamples) {
      $samples += [pscustomobject]@{
        Path = $sample.Path
        InstanceName = $sample.InstanceName
        CookedValue = [double]$sample.CookedValue
      }
    }
  } catch {
  }
}
$samples | ConvertTo-Json -Depth 5
"""
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ]
        try:
            result = self.runner.run(command, timeout=9, read_only=True)
        except Exception as exc:
            return self._snapshot("windows_counters", "Windows performance counters", False, "failed", str(exc), [])
        sensors = []
        if result.exit_code == 0 and (result.stdout or "").strip():
            try:
                parsed = json.loads(result.stdout)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                for row in parsed or []:
                    sensors.extend(self._counter_row_to_sensor(row))
            except Exception as exc:
                return self._snapshot("windows_counters", "Windows performance counters", False, "failed", f"Could not parse Get-Counter output: {exc}", [])
        status = "ok" if sensors else "no_supported_sensors_found"
        reason = "" if sensors else (result.stderr or result.error or "Windows counters returned no supported CPU telemetry.")
        return self._snapshot("windows_counters", "Windows performance counters", bool(sensors), status, reason, sensors)

    def _counter_row_to_sensor(self, row: dict[str, Any]) -> list[dict[str, Any]]:
        path = str(row.get("Path") or row.get("path") or "").lower()
        instance = str(row.get("InstanceName") or row.get("instanceName") or "_Total")
        try:
            value = float(row.get("CookedValue") if row.get("CookedValue") is not None else row.get("cookedValue"))
        except (TypeError, ValueError):
            return []
        if "% processor utility" in path:
            return [
                {
                    "source": "windows_counters",
                    "provider": "Windows performance counters",
                    "hardware": "Windows Processor Information",
                    "hardware_type": "Cpu",
                    "sensor_type": "Load",
                    "name": "Processor Utility Total" if instance.lower() == "_total" else f"Processor Utility {instance}",
                    "value": round(value, 2),
                    "unit": "%",
                    "confidence": "fallback",
                }
            ]
        if "processor frequency" in path:
            return [
                {
                    "source": "windows_counters",
                    "provider": "Windows performance counters",
                    "hardware": "Windows Processor Information",
                    "hardware_type": "Cpu",
                    "sensor_type": "Clock",
                    "name": "Processor Frequency" if instance.lower() == "_total" else f"Processor Frequency {instance}",
                    "value": round(value, 2),
                    "unit": "MHz",
                    "confidence": "fallback",
                }
            ]
        if "% processor performance" in path:
            return [
                {
                    "source": "windows_counters",
                    "provider": "Windows performance counters",
                    "hardware": "Windows Processor Information",
                    "hardware_type": "Cpu",
                    "sensor_type": "Load",
                    "name": "Processor Performance Total" if instance.lower() == "_total" else f"Processor Performance {instance}",
                    "value": round(value, 2),
                    "unit": "%",
                    "confidence": "fallback",
                    "notes": "Performance percentage fallback; not a hardware power or temperature sensor.",
                }
            ]
        return []

    def _wmi_cim_status(self) -> dict[str, Any]:
        snapshot = self.wmi_cim_thermal_snapshot()
        return {
            "status": snapshot.get("status"),
            "sensor_count": len(snapshot.get("sensors", [])),
            "error": snapshot.get("error"),
            "notes": snapshot.get("notes"),
        }

    def _acpi_status(self) -> dict[str, Any]:
        snapshot = self.acpi_thermal_snapshot()
        return {
            "status": snapshot.get("status"),
            "diagnostic_only": True,
            "sensor_count": len(snapshot.get("sensors", [])),
            "error": snapshot.get("error"),
            "notes": snapshot.get("notes"),
        }

    def wmi_cim_thermal_snapshot(self) -> dict[str, Any]:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-CimInstance -ClassName Win32_TemperatureProbe -ErrorAction SilentlyContinue | Select-Object Name,Description,CurrentReading,Status | ConvertTo-Json -Depth 4",
        ]
        try:
            result = self.runner.run(command, timeout=6, read_only=True)
        except Exception as exc:
            return self._snapshot("wmi_cim_thermal", "WMI/CIM thermal data", False, "failed", str(exc), [])
        sensors = self._parse_wmi_temperature_rows(result.stdout)
        status = "diagnostic_only" if sensors else "unavailable"
        reason = "" if sensors else (result.stderr or result.error or "WMI/CIM did not expose supported thermal probe readings.")
        return self._snapshot("wmi_cim_thermal", "WMI/CIM thermal data", bool(sensors), status, reason, sensors)

    def acpi_thermal_snapshot(self) -> dict[str, Any]:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object InstanceName,CurrentTemperature,CriticalTripPoint | ConvertTo-Json -Depth 4",
        ]
        try:
            result = self.runner.run(command, timeout=6, read_only=True)
        except Exception as exc:
            return self._snapshot("acpi_thermal", "ACPI thermal zones", False, "failed", str(exc), [])
        sensors = self._parse_acpi_temperature_rows(result.stdout)
        status = "diagnostic_only" if sensors else "unavailable"
        reason = "" if sensors else (result.stderr or result.error or "ACPI thermal zones did not expose supported readings.")
        return self._snapshot("acpi_thermal", "ACPI thermal zones", bool(sensors), status, reason, sensors)

    def _hwinfo_status(self) -> dict[str, Any]:
        snapshot = self.hwinfo_snapshot()
        return {
            "status": snapshot.get("status"),
            "shared_memory": snapshot.get("shared_memory"),
            "sensor_count": len(snapshot.get("sensors", [])),
            "error": snapshot.get("error"),
            "notes": snapshot.get("notes"),
        }

    def hwinfo_snapshot(self) -> dict[str, Any]:
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
            return self._snapshot("hwinfo", "HWiNFO shared memory", False, "failed", str(exc), [], shared_memory="unknown")
        detected = result.exit_code == 0 and bool((result.stdout or "").strip())
        if not detected:
            return self._snapshot("hwinfo", "HWiNFO shared memory", False, "not_running", "HWiNFO process is not running.", [], shared_memory="unknown")
        shared_memory = self._hwinfo_shared_memory_status()
        if not shared_memory.get("available"):
            return self._snapshot(
                "hwinfo",
                "HWiNFO shared memory",
                False,
                "not_configured",
                shared_memory.get("reason", "HWiNFO shared memory mapping is unavailable. Enable Shared Memory Support in HWiNFO settings."),
                [],
                shared_memory="unavailable",
            )
        return self._snapshot(
            "hwinfo",
            "HWiNFO shared memory",
            False,
            "not_configured",
            "HWiNFO shared memory mapping was detected, but the built-in parser could not safely decode sensor rows in this phase.",
            [],
            shared_memory="detected",
        )

    def _hwinfo_shared_memory_status(self) -> dict[str, Any]:
        if not hasattr(ctypes, "windll"):
            return {"available": False, "reason": "Shared memory probing is only available on Windows."}
        kernel32 = ctypes.windll.kernel32
        kernel32.OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
        kernel32.OpenFileMappingW.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        names = ["Global\\HWiNFO_SENS_SM2", "HWiNFO_SENS_SM2", "Global\\HWiNFO_SENS_SM", "HWiNFO_SENS_SM"]
        file_map_read = 0x0004
        for name in names:
            handle = kernel32.OpenFileMappingW(file_map_read, False, name)
            if handle:
                kernel32.CloseHandle(handle)
                return {"available": True, "mapping_name": name}
        return {"available": False, "reason": "HWiNFO shared memory mapping was not found. HWiNFO may be running with Shared Memory Support disabled."}

    def _parse_wmi_temperature_rows(self, stdout: str) -> list[dict[str, Any]]:
        if not (stdout or "").strip():
            return []
        try:
            parsed = json.loads(stdout)
        except Exception:
            return []
        if isinstance(parsed, dict):
            parsed = [parsed]
        sensors = []
        for row in parsed or []:
            name = str(row.get("Name") or row.get("Description") or "WMI thermal probe")
            raw_value = row.get("CurrentReading")
            value = self._temperature_from_wmi_value(raw_value)
            if value is None:
                continue
            is_cpu = any(term in name.lower() for term in ("cpu", "processor"))
            sensors.append(
                {
                    "source": "wmi_cim_thermal",
                    "provider": "WMI/CIM thermal data",
                    "hardware": name,
                    "hardware_type": "Cpu" if is_cpu else "ThermalZone",
                    "sensor_type": "Temperature",
                    "name": name,
                    "value": value,
                    "unit": "C",
                    "confidence": "low",
                    "notes": "Low-confidence WMI/CIM thermal diagnostic; not treated as CPU die temperature unless CPU-like.",
                }
            )
        return sensors

    def _parse_acpi_temperature_rows(self, stdout: str) -> list[dict[str, Any]]:
        if not (stdout or "").strip():
            return []
        try:
            parsed = json.loads(stdout)
        except Exception:
            return []
        if isinstance(parsed, dict):
            parsed = [parsed]
        sensors = []
        for row in parsed or []:
            name = str(row.get("InstanceName") or "ACPI thermal zone")
            value = self._temperature_from_acpi_deci_kelvin(row.get("CurrentTemperature"))
            if value is None:
                continue
            is_cpu = any(term in name.lower() for term in ("cpu", "processor"))
            sensors.append(
                {
                    "source": "acpi_thermal",
                    "provider": "ACPI thermal zones",
                    "hardware": name,
                    "hardware_type": "Cpu" if is_cpu else "AcpiThermalZone",
                    "sensor_type": "Temperature",
                    "name": name,
                    "value": value,
                    "unit": "C",
                    "confidence": "low",
                    "notes": "Low-confidence ACPI thermal zone fallback; not labeled CPU die temperature unless CPU-like.",
                }
            )
        return sensors

    def _temperature_from_wmi_value(self, raw_value: Any) -> float | None:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return None
        if value <= 0:
            return None
        if value > 1000:
            return self._temperature_from_acpi_deci_kelvin(value)
        return value

    def _temperature_from_acpi_deci_kelvin(self, raw_value: Any) -> float | None:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return None
        if value <= 0:
            return None
        celsius = (value / 10.0) - 273.15
        if celsius < -50 or celsius > 150:
            return None
        return round(celsius, 1)

    def _snapshot(
        self,
        provider_id: str,
        provider_name: str,
        ok: bool,
        status: str,
        reason: str,
        sensors: list[dict[str, Any]],
        **extra: Any,
    ) -> dict[str, Any]:
        payload = {
            "ok": ok,
            "provider_id": provider_id,
            "provider_name": provider_name,
            "source": provider_id,
            "status": status,
            "error": reason or None,
            "reason": reason,
            "sensors": sensors,
            "sensor_count": len(sensors),
        }
        payload.update(extra)
        return payload
