from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication, QComboBox, QPlainTextEdit, QPushButton, QWidget

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
    assert window.tabs.count() == 9

    cpu_selector = find_required(window, "cpu_power_source_selector")
    assert isinstance(cpu_selector, QComboBox)
    assert [cpu_selector.itemText(i) for i in range(cpu_selector.count())] == ["AC", "DC"]

    cpu_panel = find_required(window, "cpu_setting_editor")
    ac_editors = cpu_panel.findChildren(QWidget, "cpu_desired_ac_value_editor")
    dc_editors = cpu_panel.findChildren(QWidget, "cpu_desired_dc_value_editor")
    assert ac_editors, "AC view should show AC desired value editors"
    assert not dc_editors, "AC view must not show DC desired value editors"

    preview = find_required(window, "cpu_dryrun_preview")
    assert isinstance(preview, QPlainTextEdit)
    preview_text = preview.toPlainText().lower()
    assert "/setacvalueindex" in preview_text or "selected ac" in preview_text
    assert "/setdcvalueindex" not in preview_text

    cpu_selector.setCurrentText("DC")
    app.processEvents()
    cpu_panel = find_required(window, "cpu_setting_editor")
    ac_editors = cpu_panel.findChildren(QWidget, "cpu_desired_ac_value_editor")
    dc_editors = cpu_panel.findChildren(QWidget, "cpu_desired_dc_value_editor")
    assert dc_editors, "DC view should show DC desired value editors"
    assert not ac_editors, "DC view must not show AC desired value editors"
    preview_text = preview.toPlainText().lower()
    assert "/setdcvalueindex" in preview_text or "selected dc" in preview_text
    assert "/setacvalueindex" not in preview_text

    for object_name in [
        "cpu_apply_gate_status",
        "cpu_current_vs_desired_summary",
        "power_plan_management_panel",
        "power_plan_list_table",
        "power_plan_create_preview_button",
        "power_plan_set_preview_button",
        "process_command_line_table",
        "presentmon_running_state_label",
    ]:
        find_required(window, object_name)

    for button_name in ["cpu_guarded_apply_button", "power_plan_create_apply_button", "power_plan_set_apply_button"]:
        button = find_required(window, button_name)
        assert isinstance(button, QPushButton)
        assert not button.isEnabled(), f"{button_name} must stay disabled in Phase 5 unless gates are proven"

    window.close()
    print("phase5 ui contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
