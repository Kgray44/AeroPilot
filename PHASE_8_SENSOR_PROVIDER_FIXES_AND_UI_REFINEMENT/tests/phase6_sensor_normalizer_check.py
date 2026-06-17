from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.sensor_normalizer import SensorNormalizer


def lhm_snapshot(sensors: list[dict]) -> dict:
    return {"ok": True, "generated_local": "2026-06-15T18:30:00", "sensors": sensors}


def cpu_temp(name: str, value: float, hardware: str = "Intel Core Ultra", hardware_type: str = "Cpu") -> dict:
    return {
        "source": "lhm",
        "hardware": hardware,
        "hardware_type": hardware_type,
        "sensor_type": "Temperature",
        "name": name,
        "value": value,
        "min": value - 3,
        "max": value + 4,
    }


def normalize(sensors: list[dict], nvidia: dict | None = None, presentmon: dict | None = None) -> dict:
    return SensorNormalizer().normalize(
        lhm_snapshot(sensors),
        nvidia_snapshot=nvidia or {"ok": True, "data": {}},
        presentmon_snapshot=presentmon or {"ok": True, "fps": None, "frame_time_ms": None},
        favorites={"favorites": []},
    )


def assert_cpu_temp_selected(name: str, value: float) -> None:
    model = normalize([cpu_temp(name, value)])
    assert model["ok"] is True
    assert model["headline"]["cpu_temp_c"] == value
    assert model["headline"]["cpu_temp_name"] == name
    selected = [row for row in model["raw_sensors"] if row.get("selected_for_headline")]
    assert selected and selected[0]["name"] == name
    assert model["groups"]["cpu"], "CPU group should contain the selected CPU sensor"


def test_cpu_temperature_priority_names_are_selected() -> None:
    for name in ["CPU Package", "Package", "Core Max", "P-Core Max", "Tctl/Tdie"]:
        assert_cpu_temp_selected(name, 58.0)


def test_cpu_temperature_prefers_package_over_hotter_core() -> None:
    model = normalize([cpu_temp("Core 7", 71.0), cpu_temp("CPU Package", 61.0)])
    assert model["headline"]["cpu_temp_name"] == "CPU Package"
    assert model["headline"]["cpu_temp_c"] == 61.0


def test_cpu_temperature_falls_back_to_highest_valid_cpu_temperature() -> None:
    model = normalize([cpu_temp("Core 1", 47.0), cpu_temp("Core 2", 55.0), cpu_temp("Core 3", 51.0)])
    assert model["headline"]["cpu_temp_name"] == "Core 2"
    assert model["headline"]["cpu_temp_c"] == 55.0


def test_cpu_temperature_rejects_invalid_values_and_explains_failure() -> None:
    sensors = [cpu_temp("CPU Package", 0.0), cpu_temp("Core Max", 129.0), cpu_temp("GPU Core", 64.0, "NVIDIA GPU", "Gpu")]
    model = normalize(sensors)
    assert model["headline"]["cpu_temp_c"] is None
    assert model["headline"]["cpu_temp_display"] == "CPU temp unavailable"
    diagnostics = model["diagnostics"]
    assert diagnostics["cpu_temperature"]["selected"] is None
    assert diagnostics["cpu_temperature"]["total_temperature_sensors"] == 3
    assert diagnostics["cpu_temperature"]["cpu_hardware_temperature_sensors"] == 2
    rejected = diagnostics["cpu_temperature"]["rejected_candidates"]
    assert any("invalid temperature" in row["reason"].lower() for row in rejected)


def test_raw_sensors_preserved_and_grouped_for_common_hardware() -> None:
    sensors = [
        cpu_temp("CPU Package", 58.0),
        {"hardware": "Intel Core Ultra", "hardware_type": "Cpu", "sensor_type": "Load", "name": "CPU Total", "value": 7.2},
        {"hardware": "Intel Core Ultra", "hardware_type": "Cpu", "sensor_type": "Power", "name": "CPU Package", "value": 18.5},
        {"hardware": "Memory", "hardware_type": "Memory", "sensor_type": "Load", "name": "Memory", "value": 42.0},
        {"hardware": "NVMe Drive", "hardware_type": "Storage", "sensor_type": "Temperature", "name": "Temperature", "value": 45.0},
        {"hardware": "Board", "hardware_type": "Motherboard", "sensor_type": "Fan", "name": "Fan #1", "value": 4200},
    ]
    model = normalize(sensors, nvidia={"ok": True, "data": {"temperature.gpu": 55, "utilization.gpu": 1, "power.draw": 11, "clocks.gr": 210}})
    assert len(model["raw_sensors"]) == len(sensors) + 4
    assert model["headline"]["cpu_load_percent"] == 7.2
    assert model["headline"]["cpu_power_w"] == 18.5
    assert model["headline"]["fan_rpm"] == 4200.0
    assert model["headline"]["gpu_temp_c"] == 55.0
    assert model["groups"]["memory"]
    assert model["groups"]["storage"]
    assert model["groups"]["fans"]


def main() -> int:
    tests = [
        test_cpu_temperature_priority_names_are_selected,
        test_cpu_temperature_prefers_package_over_hotter_core,
        test_cpu_temperature_falls_back_to_highest_valid_cpu_temperature,
        test_cpu_temperature_rejects_invalid_values_and_explains_failure,
        test_raw_sensors_preserved_and_grouped_for_common_hardware,
    ]
    for test in tests:
        test()
    print("phase6 sensor normalizer contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
