from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.sensor_normalizer import SensorNormalizer
from app.core.sensor_presentation import SensorPresentation


def make_model() -> dict:
    lhm = {
        "ok": True,
        "generated_local": "2026-06-15T21:00:00",
        "sensors": [
            {"source": "lhm", "hardware": "Intel Core Ultra", "hardware_type": "Cpu", "sensor_type": "Temperature", "name": "CPU Package", "value": 54},
            {"source": "lhm", "hardware": "Intel Core Ultra", "hardware_type": "Cpu", "sensor_type": "Load", "name": "CPU Total", "value": 7},
            {"source": "lhm", "hardware": "Intel Core Ultra", "hardware_type": "Cpu", "sensor_type": "Power", "name": "CPU Package", "value": 16.2},
            {"source": "lhm", "hardware": "Intel Core Ultra", "hardware_type": "Cpu", "sensor_type": "Clock", "name": "Core Effective Clock", "value": 2100},
            {"source": "lhm", "hardware": "Memory", "hardware_type": "Memory", "sensor_type": "Load", "name": "Memory", "value": 41},
            {"source": "lhm", "hardware": "NVMe SSD", "hardware_type": "Storage", "sensor_type": "Temperature", "name": "Temperature", "value": 43},
            {"source": "lhm", "hardware": "Board", "hardware_type": "Motherboard", "sensor_type": "Fan", "name": "Fan #1", "value": 4200},
        ],
    }
    nvidia = {
        "ok": True,
        "data": {
            "name": "NVIDIA GeForce RTX 5070 Laptop GPU",
            "temperature.gpu": 55,
            "utilization.gpu": 4,
            "power.draw": 12,
            "clocks.current.graphics": 210,
            "memory.used": 1348,
            "memory.total": 8151,
        },
    }
    presentmon = {"ok": True, "status": "idle", "fps_average_sample": 60, "frametime_ms_average_sample": 16.7, "latest_process": "BF6.exe"}
    return SensorNormalizer().normalize(lhm, nvidia, presentmon, {"favorites": []})


def test_presentation_builds_four_primary_hero_cards_without_low_priority_cards() -> None:
    presentation = SensorPresentation(make_model(), history={}).build()
    hero_titles = [card["title"] for card in presentation["hero_cards"]]
    assert hero_titles == ["CPU", "GPU", "Memory / VRAM", "Frames"]
    assert "Sensor Count" not in hero_titles
    assert "Read Status" not in hero_titles
    for card in presentation["hero_cards"]:
        assert card.get("value_display") != card.get("subtitle"), card


def test_status_pills_hold_readiness_and_counts() -> None:
    presentation = SensorPresentation(make_model(), history={}, polling_active=False).build()
    labels = [pill["label"] for pill in presentation["status_pills"]]
    assert "LHM" in labels
    assert "NVIDIA" in labels
    assert "PresentMon" in labels
    assert "Raw sensors" in labels
    assert "Polling" in labels
    assert any(pill["label"] == "Raw sensors" and str(pill["value"]).isdigit() for pill in presentation["status_pills"])


def test_raw_table_rows_preserve_every_sensor_with_readable_columns() -> None:
    model = make_model()
    presentation = SensorPresentation(model, history={}).build()
    assert len(presentation["raw_table_rows"]) == len(model["raw_sensors"])
    first = presentation["raw_table_rows"][0]
    expected_first_columns = ["favorite", "selected", "category", "hardware", "sensor_type", "name", "value", "unit", "notes"]
    assert list(first.keys())[: len(expected_first_columns)] == expected_first_columns


def test_cpu_diagnostics_explains_unavailable_temperature() -> None:
    model = SensorNormalizer().normalize(
        {"ok": True, "sensors": [{"hardware": "Intel Core Ultra", "hardware_type": "Cpu", "sensor_type": "Temperature", "name": "Core (Tctl/Tdie)", "value": 0}]},
        {"ok": False},
        {"ok": True, "status": "idle"},
        {"favorites": []},
    )
    diagnostics = SensorPresentation(model, history={}).build()["diagnostics"]
    assert diagnostics["cpu_temperature"]["selected"] is None
    assert "invalid" in diagnostics["cpu_temperature"]["warning"].lower()
    assert diagnostics["cpu_temperature"]["rejected_by_reason"]["invalid temperature"]


def main() -> int:
    test_presentation_builds_four_primary_hero_cards_without_low_priority_cards()
    test_status_pills_hold_readiness_and_counts()
    test_raw_table_rows_preserve_every_sensor_with_readable_columns()
    test_cpu_diagnostics_explains_unavailable_temperature()
    print("phase7 sensor presentation contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
