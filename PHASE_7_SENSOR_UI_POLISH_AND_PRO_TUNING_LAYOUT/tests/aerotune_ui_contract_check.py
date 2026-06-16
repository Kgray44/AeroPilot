from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication, QComboBox, QWidget

from app import APP_NAME
from app.core.app_paths import AppPaths
from app.ui.main_window import MainWindow


def find_required(root: QWidget, object_name: str) -> QWidget:
    widget = root.findChild(QWidget, object_name)
    if widget is None:
        raise AssertionError(f"Missing widget objectName={object_name}")
    return widget


def main() -> int:
    assert APP_NAME == "AeroTune"
    app = QApplication.instance() or QApplication([])
    window = MainWindow(AppPaths.discover())
    assert window.windowTitle() == "AeroTune"

    for object_name in [
        "cpu_setting_editor",
        "gpu_slot_editor",
        "game_rule_editor",
        "experiment_plan_editor",
        "always_visible_telemetry_strip",
        "presentmon_readings_panel",
        "librehardwaremonitor_readings_panel",
        "nvidia_readings_panel",
    ]:
        find_required(window, object_name)

    for object_name in [
        "cpu_boost_mode_ac_editor",
        "cpu_boost_mode_dc_editor",
        "cpu_cooling_policy_ac_editor",
        "cpu_cooling_policy_dc_editor",
    ]:
        widget = find_required(window, object_name)
        assert isinstance(widget, QComboBox), f"{object_name} should be a dropdown"

    capture_script = Path(__file__).resolve().parents[1] / "scripts" / "capture_page_photos.py"
    assert capture_script.exists(), "scripts/capture_page_photos.py is required"
    print("aerotune ui contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
