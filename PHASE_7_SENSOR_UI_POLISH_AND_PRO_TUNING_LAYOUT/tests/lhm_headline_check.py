from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.adapters.librehardwaremonitor_adapter import LibreHardwareMonitorAdapter


def make_snapshot(sensors: list[dict]) -> dict:
    return {"ok": True, "sensors": sensors}


def main() -> int:
    adapter = LibreHardwareMonitorAdapter({})

    package = adapter.headline(
        make_snapshot(
            [
                {"hardware": "Intel CPU", "hardware_type": "Cpu", "name": "CPU Package", "sensor_type": "Temperature", "value": 54},
                {"hardware": "Intel CPU", "hardware_type": "Cpu", "name": "CPU Total", "sensor_type": "Load", "value": 7.2},
            ]
        )
    )
    assert package["cpu_temp_c"] == 54.0
    assert package["cpu_temp_name"] == "CPU Package"
    assert package["cpu_temp_display"] == "54 C Package"
    assert package["cpu_load_display"] == "Load 7%"
    assert package["fan_display"] == "Fan unavailable"
    assert "CPU CPU" not in package["status_display"]

    core_max = adapter.headline(
        make_snapshot(
            [
                {"hardware": "Intel CPU", "hardware_type": "Cpu", "name": "Core 1", "sensor_type": "Temperature", "value": 50},
                {"hardware": "Intel CPU", "hardware_type": "Cpu", "name": "Core Max", "sensor_type": "Temperature", "value": 61},
            ]
        )
    )
    assert core_max["cpu_temp_c"] == 61.0
    assert core_max["cpu_temp_name"] == "Core Max"
    assert "Core Max" in core_max["cpu_temp_display"]

    no_temp_sensors = [
        {"hardware": "Intel CPU", "hardware_type": "Cpu", "name": f"CPU Core {i}", "sensor_type": "Load", "value": 5}
        for i in range(139)
    ]
    no_temp = adapter.headline(make_snapshot(no_temp_sensors))
    assert no_temp["cpu_temp_c"] is None
    assert no_temp["fan_display"] == "Fan unavailable"
    assert no_temp["sensor_count"] == 139
    assert no_temp["status_display"].startswith("CPU temp unavailable")
    assert "139 readings" in no_temp["status_display"]
    assert "CPU CPU temp n/a" not in no_temp["status_display"]

    fan = adapter.headline(
        make_snapshot(
            [
                {"hardware": "Intel CPU", "hardware_type": "Cpu", "name": "CPU Package", "sensor_type": "Temperature", "value": 54},
                {"hardware": "Board", "hardware_type": "Motherboard", "name": "Fan #1", "sensor_type": "Fan", "value": 4200},
            ]
        )
    )
    assert fan["fan_rpm"] == 4200.0
    assert fan["fan_display"] == "Fan 4200 RPM"

    print("lhm headline contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
