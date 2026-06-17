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
from app.core.sensor_normalizer import SensorNormalizer
from app.ui.main_window import MainWindow
from app.ui.telemetry_widgets import MetricCard


def find_required(root: QWidget, object_name: str) -> QWidget:
    widget = root.findChild(QWidget, object_name)
    if widget is None:
        raise AssertionError(f"Missing widget objectName={object_name}")
    return widget


def main() -> int:
    assert APP_NAME == "AeroTune"
    assert APP_PHASE == "PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS"
    app = QApplication.instance() or QApplication([])
    window = MainWindow(AppPaths.discover())
    assert window.tabs.count() == 9
    assert "Sensors" in [window.tabs.tabText(index) for index in range(window.tabs.count())]

    overview = find_required(window, "sensor_overview_cards")
    raw_table = find_required(window, "sensor_raw_explorer_table")
    cpu_diag = find_required(window, "sensor_cpu_diagnostics_table")
    find_required(window, "sensor_pause_resume_button")
    assert isinstance(raw_table, QTableWidget)
    assert isinstance(cpu_diag, QTableWidget)
    assert overview.findChildren(MetricCard), "Sensors overview should contain MetricCard widgets"
    assert "CPU CPU" not in window.cpu_label.text()
    assert not window.presentmon.is_running(), "PresentMon must not start automatically"

    model = SensorNormalizer().normalize(
        {"ok": True, "sensors": [{"hardware": "Intel CPU", "hardware_type": "Cpu", "sensor_type": "Temperature", "name": "CPU Package", "value": 54}]},
        {"ok": True, "data": {"temperature.gpu": 55, "utilization.gpu": 1, "power.draw": 11, "memory.used": 1000, "memory.total": 8000}},
        {"ok": True, "fps_average_sample": 60, "frametime_ms_average_sample": 16.7},
        {"favorites": []},
    )
    status = model["headline"]["status_display"]
    assert "CPU CPU" not in status
    assert model["headline"]["cpu_temp_c"] == 54
    assert len(model["raw_sensors"]) == 8

    window.close()
    app.quit()
    print("phase6 ui contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
