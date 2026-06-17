from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.sensor_normalizer import SensorNormalizer
from app.core.telemetry_provider_registry import ProviderStatus, TelemetryProviderRegistry


CPU_HW = "AMD Ryzen AI 7 350 w/ Radeon 860M"


def lhm_partial_snapshot() -> dict:
    return {
        "ok": True,
        "source": "librehardwaremonitor",
        "sensors": [
            {"source": "lhm", "hardware": CPU_HW, "hardware_type": "Cpu", "sensor_type": "Load", "name": "CPU Total", "value": 22.0},
            {"source": "lhm", "hardware": CPU_HW, "hardware_type": "Cpu", "sensor_type": "Temperature", "name": "Core (Tctl/Tdie)", "value": 0.0},
            {"source": "lhm", "hardware": CPU_HW, "hardware_type": "Cpu", "sensor_type": "Power", "name": "Package", "value": 0.0},
            {"source": "lhm", "hardware": CPU_HW, "hardware_type": "Cpu", "sensor_type": "Clock", "name": "Cores (Average Effective)", "value": 0.0},
            {"source": "lhm", "hardware": CPU_HW, "hardware_type": "Cpu", "sensor_type": "Voltage", "name": "Core VID", "value": 1.55},
        ],
    }


def hwinfo_cpu_snapshot() -> dict:
    return {
        "ok": True,
        "provider_id": "hwinfo",
        "provider_name": "HWiNFO shared memory",
        "status": "ok",
        "sensors": [
            {"source": "hwinfo", "provider": "HWiNFO shared memory", "hardware": CPU_HW, "hardware_type": "Cpu", "sensor_type": "Temperature", "name": "CPU Package", "value": 61.0},
            {"source": "hwinfo", "provider": "HWiNFO shared memory", "hardware": CPU_HW, "hardware_type": "Cpu", "sensor_type": "Power", "name": "CPU Package Power", "value": 24.5},
            {"source": "hwinfo", "provider": "HWiNFO shared memory", "hardware": CPU_HW, "hardware_type": "Cpu", "sensor_type": "Clock", "name": "Core Effective Clock", "value": 2980.0},
        ],
    }


def windows_counter_snapshot() -> dict:
    return {
        "ok": True,
        "provider_id": "windows_counters",
        "provider_name": "Windows performance counters",
        "status": "ok",
        "sensors": [
            {"source": "windows_counters", "provider": "Windows performance counters", "hardware": "Windows Processor Information", "hardware_type": "Cpu", "sensor_type": "Load", "name": "Processor Utility Total", "value": 31.0},
            {"source": "windows_counters", "provider": "Windows performance counters", "hardware": "Windows Processor Information", "hardware_type": "Cpu", "sensor_type": "Clock", "name": "Processor Frequency", "value": 3200.0},
        ],
    }


def provider_statuses_for(*ids: str) -> list[ProviderStatus]:
    statuses = []
    for provider_id in ids:
        statuses.append(
            ProviderStatus(
                provider_id=provider_id,
                provider_name=provider_id,
                enabled=True,
                attempted=True,
                available=True,
                status="ok",
                reason="fixture",
                sensor_count=1,
                valid_sensor_count=1,
                rejected_sensor_count=0,
            )
        )
    return statuses


def test_lhm_only_fixture_does_not_show_bad_cpu_zeros_as_real_metrics() -> None:
    model = SensorNormalizer().normalize(provider_snapshots={"librehardwaremonitor": lhm_partial_snapshot()})
    headline = model["headline"]
    assert headline["cpu_temp_c"] is None
    assert headline["cpu_power_w"] is None
    assert headline["cpu_clock_mhz"] is None
    assert headline["cpu_load_percent"] == 22.0
    assert "Power 0" not in headline["status_display"]
    assert "Clock 0" not in headline["status_display"]
    statuses = model["diagnostics"]["provider_statuses"]
    assert "librehardwaremonitor" in statuses
    assert statuses["librehardwaremonitor"]["attempted"] is True
    assert statuses["librehardwaremonitor"]["status"] == "partial"


def test_hwinfo_valid_cpu_temperature_outranks_bad_lhm_temperature() -> None:
    model = SensorNormalizer().normalize(
        provider_snapshots={
            "librehardwaremonitor": lhm_partial_snapshot(),
            "hwinfo": hwinfo_cpu_snapshot(),
        },
        provider_statuses=provider_statuses_for("librehardwaremonitor", "hwinfo"),
    )
    headline = model["headline"]
    assert headline["cpu_temp_c"] == 61.0
    assert headline["cpu_power_w"] == 24.5
    assert headline["cpu_clock_mhz"] == 2980.0
    assert headline["selected_headline_metrics"]["cpu_temperature_c"]["source"] == "hwinfo"
    assert model["diagnostics"]["fallback_chain_used"]["cpu_temperature_c"][0]["source"] == "hwinfo"


def test_windows_counter_cpu_load_is_allowed_as_fallback() -> None:
    model = SensorNormalizer().normalize(
        provider_snapshots={
            "librehardwaremonitor": {"ok": False, "error": "not available", "sensors": []},
            "windows_counters": windows_counter_snapshot(),
        },
        provider_statuses=provider_statuses_for("librehardwaremonitor", "windows_counters"),
    )
    headline = model["headline"]
    assert headline["cpu_load_percent"] == 31.0
    assert headline["selected_headline_metrics"]["cpu_load_percent"]["source"] == "windows_counters"
    assert model["diagnostics"]["provider_statuses"]["windows_counters"]["attempted"] is True


def test_provider_registry_attempts_enabled_providers_and_preserves_not_attempted_state() -> None:
    registry = TelemetryProviderRegistry()
    registry.register_static_provider("attempted", "Attempted provider", lambda: {"ok": False, "error": "not installed", "sensors": []})
    registry.register_static_provider("disabled", "Disabled provider", lambda: {"ok": True, "sensors": []}, enabled=False)
    result = registry.refresh()
    assert result["provider_statuses"]["attempted"].attempted is True
    assert result["provider_statuses"]["attempted"].status in ("unavailable", "failed")
    assert result["provider_statuses"]["disabled"].attempted is False
    assert result["provider_statuses"]["disabled"].status == "not_configured"


def test_cpu_diagnostics_export_model_contains_provider_pipeline_sections() -> None:
    model = SensorNormalizer().normalize(
        provider_snapshots={
            "librehardwaremonitor": lhm_partial_snapshot(),
            "hwinfo": {"ok": False, "status": "not_running", "error": "HWiNFO process is not running.", "sensors": []},
            "windows_counters": windows_counter_snapshot(),
        },
    )
    diagnostics = model["diagnostics"]["cpu_temperature"]
    assert "provider_statuses" in diagnostics
    assert "all_provider_sensors" in diagnostics
    assert "accepted_candidates" in diagnostics
    assert "rejected_candidates" in diagnostics
    assert "selected_headline_metrics" in diagnostics
    assert "fallback_chain_used" in diagnostics
    assert "unavailable_reasons_by_metric" in diagnostics
    assert diagnostics["provider_statuses"]["hwinfo"]["status"] in ("unavailable", "not_configured", "not_running")
    assert diagnostics["unavailable_reasons_by_metric"]["cpu_temperature_c"]
    assert diagnostics["next_recommended_action"] == "Start HWiNFO64 Sensors with shared memory enabled."
    explanation = "\n".join(diagnostics["fallback_explanation"])
    assert "LHM rejected Core (Tctl/Tdie) because it reported 0 C" in explanation
    assert "HWiNFO" in explanation and ("not running" in explanation or "shared memory" in explanation)
    assert "Windows counters are available for CPU load/frequency" in explanation
    assert "WMI/CIM thermal unavailable" in explanation
    assert "ACPI thermal unavailable" in explanation


def main() -> int:
    test_lhm_only_fixture_does_not_show_bad_cpu_zeros_as_real_metrics()
    test_hwinfo_valid_cpu_temperature_outranks_bad_lhm_temperature()
    test_windows_counter_cpu_load_is_allowed_as_fallback()
    test_provider_registry_attempts_enabled_providers_and_preserves_not_attempted_state()
    test_cpu_diagnostics_export_model_contains_provider_pipeline_sections()
    print("phase8 provider pipeline contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
