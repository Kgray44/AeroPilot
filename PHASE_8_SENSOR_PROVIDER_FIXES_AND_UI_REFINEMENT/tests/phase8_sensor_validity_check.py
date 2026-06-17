from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.sensor_normalizer import SensorNormalizer
from app.core.sensor_presentation import SensorPresentation


def lhm_snapshot(sensors: list[dict]) -> dict:
    return {"ok": True, "generated_local": "2026-06-15T21:04:00", "sensors": sensors}


def cpu_snapshot() -> dict:
    hardware = "AMD Ryzen AI 7 350 w/ Radeon 860M"
    return lhm_snapshot(
        [
            {"source": "lhm", "hardware": hardware, "hardware_type": "Cpu", "sensor_type": "Load", "name": "CPU Total", "value": 23.4},
            {"source": "lhm", "hardware": hardware, "hardware_type": "Cpu", "sensor_type": "Load", "name": "CPU Core Max", "value": 42.0},
            {"source": "lhm", "hardware": hardware, "hardware_type": "Cpu", "sensor_type": "Temperature", "name": "Core (Tctl/Tdie)", "value": 0.0},
            {"source": "lhm", "hardware": hardware, "hardware_type": "Cpu", "sensor_type": "Power", "name": "Package", "value": 0.0},
            {"source": "lhm", "hardware": hardware, "hardware_type": "Cpu", "sensor_type": "Power", "name": "Core SMU", "value": 0.0},
            {"source": "lhm", "hardware": hardware, "hardware_type": "Cpu", "sensor_type": "Clock", "name": "Cores (Average Effective)", "value": 0.0},
            {"source": "lhm", "hardware": hardware, "hardware_type": "Cpu", "sensor_type": "Voltage", "name": "Core VID", "value": 1.55},
        ]
    )


def normalize_cpu() -> dict:
    return SensorNormalizer().normalize(cpu_snapshot(), {"ok": False}, {"ok": True, "status": "idle"}, {"favorites": []})


def row_by_name(model: dict, name: str) -> dict:
    for row in model["raw_sensors"]:
        if row.get("name") == name:
            return row
    raise AssertionError(f"missing row {name}")


def test_cpu_stale_zero_and_invalid_values_are_not_headline_metrics() -> None:
    model = normalize_cpu()
    headline = model["headline"]
    assert headline["cpu_load_percent"] == 23.4
    assert headline["cpu_temp_c"] is None
    assert headline["cpu_power_w"] is None
    assert headline["cpu_clock_mhz"] is None
    assert headline["cpu_voltage_v"] == 1.55
    assert "CPU Load 23%" in headline["status_display"]
    assert "Temp unavailable" in headline["status_display"]
    assert "Power unavailable" in headline["status_display"]
    assert "Power 0" not in headline["status_display"]
    assert "Clock 0" not in headline["status_display"]

    temp = row_by_name(model, "Core (Tctl/Tdie)")
    power = row_by_name(model, "Package")
    clock = row_by_name(model, "Cores (Average Effective)")
    voltage = row_by_name(model, "Core VID")
    assert temp["validity"] == "invalid_value"
    assert "0 C" in temp["validity_reason"]
    assert power["validity"] == "stale_zero"
    assert clock["validity"] == "stale_zero"
    assert voltage["validity"] == "valid"
    assert voltage["display_value"].endswith(" V")
    for row in (temp, power, clock, voltage):
        assert "display_status" in row
        assert "can_use_for_headline" in row
        assert "can_use_for_card" in row


def test_cpu_presentation_uses_load_when_temperature_is_invalid() -> None:
    model = normalize_cpu()
    presentation = SensorPresentation(model, history={}).build()
    cpu_card = next(card for card in presentation["hero_cards"] if card["key"] == "cpu")
    assert cpu_card["value_display"] == "23"
    assert cpu_card["unit"] == "%"
    assert "CPU load" in cpu_card["subtitle"]
    chip_text = " ".join(f"{chip['label']} {chip['value']}" for chip in cpu_card["chips"])
    assert "Temp unavailable" in chip_text
    assert "Power unavailable" in chip_text
    assert "Clock unavailable" in chip_text
    assert "VID 1.55 V" in chip_text
    assert "0 W" not in chip_text
    assert "0 MHz" not in chip_text


def test_cpu_diagnostics_explain_partial_provider_health() -> None:
    diagnostics = SensorPresentation(normalize_cpu(), history={}).build()["diagnostics"]
    cpu = diagnostics["cpu_temperature"]
    assert "CPU telemetry is partial" in cpu["provider_summary"]
    assert cpu["metric_health"]["load"]["validity"] == "valid"
    assert cpu["metric_health"]["temperature"]["validity"] == "invalid_value"
    assert cpu["metric_health"]["power"]["validity"] == "stale_zero"
    assert cpu["metric_health"]["clock"]["validity"] == "stale_zero"
    assert cpu["metric_health"]["voltage"]["validity"] == "valid"
    assert cpu["stale_zero_cpu_sensors"]
    assert cpu["invalid_cpu_sensors"]
    assert "HWiNFO" in cpu["provider_recommendation"]


def test_gpu_lhm_hardware_types_and_invalid_values_are_classified() -> None:
    model = SensorNormalizer().normalize(
        lhm_snapshot(
            [
                {"source": "lhm", "hardware": "NVIDIA GeForce RTX 5070 Laptop GPU", "hardware_type": "GpuNvidia", "sensor_type": "Temperature", "name": "GPU Core", "value": 54},
                {"source": "lhm", "hardware": "NVIDIA GeForce RTX 5070 Laptop GPU", "hardware_type": "GpuNvidia", "sensor_type": "Temperature", "name": "GPU Memory Junction", "value": 255},
                {"source": "lhm", "hardware": "NVIDIA GeForce RTX 5070 Laptop GPU", "hardware_type": "GpuNvidia", "sensor_type": "Clock", "name": "GPU Core", "value": 210},
                {"source": "lhm", "hardware": "NVIDIA GeForce RTX 5070 Laptop GPU", "hardware_type": "GpuNvidia", "sensor_type": "Clock", "name": "GPU Memory", "value": 810},
                {"source": "lhm", "hardware": "NVIDIA GeForce RTX 5070 Laptop GPU", "hardware_type": "GpuNvidia", "sensor_type": "Load", "name": "GPU Core", "value": 1},
                {"source": "lhm", "hardware": "AMD Radeon 860M", "hardware_type": "GpuAmd", "sensor_type": "Load", "name": "GPU Core", "value": 2},
            ]
        ),
        {"ok": False},
        {"ok": True, "status": "idle"},
        {"favorites": []},
    )
    gpu_rows = [row for row in model["raw_sensors"] if row.get("category") == "gpu"]
    assert len(gpu_rows) == 6
    assert any(row.get("subcategory") == "dgpu" for row in gpu_rows)
    assert any(row.get("subcategory") == "igpu" for row in gpu_rows)
    keys = {row.get("normalized_key") for row in gpu_rows}
    assert "gpu_core_temp_c" in keys
    assert "gpu_memory_junction_temp_c" in keys
    assert "gpu_core_clock_mhz" in keys
    assert "gpu_memory_clock_mhz" in keys
    junction = row_by_name(model, "GPU Memory Junction")
    assert junction["validity"] == "invalid_value"
    assert junction["can_use_for_headline"] is False


def test_generic_memory_units_do_not_render_gb_values_as_mb() -> None:
    model = SensorNormalizer().normalize(
        lhm_snapshot(
            [
                {"source": "lhm", "hardware": "Generic Memory", "hardware_type": "Memory", "sensor_type": "Data", "name": "Memory Used", "value": 18.6},
                {"source": "lhm", "hardware": "Generic Memory", "hardware_type": "Memory", "sensor_type": "Data", "name": "Memory Available", "value": 13.4},
            ]
        ),
        {"ok": False},
        {"ok": True, "status": "idle"},
        {"favorites": []},
    )
    used = row_by_name(model, "Memory Used")
    assert used["display_value"].endswith(" GB")
    assert "MB" not in used["display_value"]


def main() -> int:
    test_cpu_stale_zero_and_invalid_values_are_not_headline_metrics()
    test_cpu_presentation_uses_load_when_temperature_is_invalid()
    test_cpu_diagnostics_explain_partial_provider_health()
    test_gpu_lhm_hardware_types_and_invalid_values_are_classified()
    test_generic_memory_units_do_not_render_gb_values_as_mb()
    print("phase8 sensor validity contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
