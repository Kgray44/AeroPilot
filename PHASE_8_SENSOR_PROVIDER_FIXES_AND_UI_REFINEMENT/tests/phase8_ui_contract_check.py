from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget, QWidget

from app import APP_NAME, APP_PHASE
from app.core.app_paths import AppPaths
from app.ui.main_window import MainWindow


def find_required(root: QWidget, object_name: str) -> QWidget:
    widget = root.findChild(QWidget, object_name)
    if widget is None:
        raise AssertionError(f"Missing widget objectName={object_name}")
    return widget


def table_headers(table: QTableWidget) -> list[str]:
    return [table.horizontalHeaderItem(index).text() for index in range(table.columnCount())]


def main() -> int:
    assert APP_NAME == "AeroTune"
    assert APP_PHASE == "PHASE_8_SENSOR_PROVIDER_FIXES_AND_UI_REFINEMENT"
    app = QApplication.instance() or QApplication([])
    window = MainWindow(AppPaths.discover())
    assert window.tabs.count() == 9
    assert "Sensors" in [window.tabs.tabText(index) for index in range(window.tabs.count())]

    sensor_tab = window.tabs.widget(3)
    find_required(sensor_tab, "sensor_provider_status_section")
    raw_table = find_required(sensor_tab, "sensor_all_raw_explorer_table")
    assert isinstance(raw_table, QTableWidget)
    headers = table_headers(raw_table)
    assert "Validity" in headers
    assert "Validity reason" in headers
    assert "Provider" in headers
    assert "Subcategory" in headers

    find_required(sensor_tab, "sensor_cpu_diagnostics_panel")
    guidance = find_required(sensor_tab, "sensor_cpu_temp_guidance_block")
    guidance_text = guidance.property("guidanceText") or guidance.toolTip() or ""
    assert "Start HWiNFO64 Sensors" in guidance_text
    assert "shared memory" in guidance_text
    export_button = find_required(sensor_tab, "sensor_export_cpu_diagnostics_button")
    assert isinstance(export_button, QPushButton)
    assert "CPU CPU" not in window.cpu_label.text()
    assert not window.presentmon.is_running(), "PresentMon must not start automatically"

    window.close()
    app.quit()
    print("phase8 ui contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
