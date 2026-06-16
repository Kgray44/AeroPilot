from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication, QTableWidget, QWidget

from app import APP_NAME, APP_PHASE
from app.core.app_paths import AppPaths
from app.ui.main_window import MainWindow
from app.ui.telemetry_widgets import HardwarePanel, HeroMetricCard, StatusPill


def find_required(root: QWidget, object_name: str) -> QWidget:
    widget = root.findChild(QWidget, object_name)
    if widget is None:
        raise AssertionError(f"Missing widget objectName={object_name}")
    return widget


def main() -> int:
    assert APP_NAME == "AeroTune"
    assert APP_PHASE == "PHASE_7_SENSOR_UI_POLISH_AND_PRO_TUNING_LAYOUT"
    app = QApplication.instance() or QApplication([])
    window = MainWindow(AppPaths.discover())
    assert window.tabs.count() == 9
    assert "Sensors" in [window.tabs.tabText(index) for index in range(window.tabs.count())]

    sensor_tab = window.tabs.widget(3)
    hero_strip = find_required(sensor_tab, "sensor_hero_strip")
    hero_cards = hero_strip.findChildren(HeroMetricCard)
    assert len(hero_cards) == 4
    hero_titles = [card.title_label.text() for card in hero_cards]
    assert "Sensor Count" not in hero_titles
    assert "Read Status" not in hero_titles
    for card in hero_cards:
        assert card.value_label.text() != card.subtitle_label.text()

    pills = find_required(sensor_tab, "sensor_status_pills")
    assert len(pills.findChildren(StatusPill)) >= 5

    hardware_panels = find_required(sensor_tab, "sensor_hardware_panels")
    assert len(hardware_panels.findChildren(HardwarePanel)) >= 6
    assert len(hardware_panels.findChildren(QTableWidget)) <= 2

    raw_table = find_required(sensor_tab, "sensor_all_raw_explorer_table")
    assert isinstance(raw_table, QTableWidget)
    find_required(sensor_tab, "sensor_raw_count_label")
    find_required(sensor_tab, "sensor_cpu_diagnostics_panel")
    accepted = find_required(sensor_tab, "sensor_cpu_accepted_candidates_panel")
    assert accepted.minimumHeight() >= 180
    assert "CPU CPU" not in window.cpu_label.text()
    assert not window.presentmon.is_running(), "PresentMon must not start automatically"

    window.close()
    app.quit()
    print("phase7 ui contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
