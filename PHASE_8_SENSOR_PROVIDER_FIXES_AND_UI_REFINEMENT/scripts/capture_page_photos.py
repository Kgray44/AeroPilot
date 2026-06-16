from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QComboBox, QScrollArea

from app import APP_NAME
from app.core.app_paths import AppPaths
from app.ui.main_window import MainWindow


def close_popups(window: MainWindow, app: QApplication) -> None:
    popup = app.activePopupWidget()
    if popup is not None:
        popup.close()
    for combo in window.findChildren(QComboBox):
        combo.hidePopup()
    app.processEvents()


PHOTO_PLAN = [
    (0, "01_dashboard.png", None, None, 0),
    (1, "02_cpu_presets_ac.png", "AC", None, 0),
    (1, "03_cpu_presets_dc.png", "DC", None, 0),
    (2, "04_gpu_profiles.png", None, None, 0),
    (3, "05_sensors_overview_refined.png", None, "show_overview", 0),
    (3, "06_sensors_cpu_partial_provider.png", None, "show_hardware_panels", 620),
    (3, "07_sensors_gpu_panels.png", None, "show_hardware_panels", 900),
    (3, "08_sensors_all_raw_validity.png", None, "show_raw_explorer", 1600),
    (3, "09_sensors_cpu_diagnostics.png", None, "show_cpu_diagnostics", 3300),
    (4, "10_game_automation.png", None, None, 0),
    (5, "11_auto_tuning.png", None, None, 0),
    (6, "12_fan_experimental.png", None, None, 0),
    (7, "13_logs.png", None, None, 0),
    (8, "14_settings.png", None, None, 0),
]


def main() -> int:
    paths = AppPaths.discover()
    output_dir = paths.phase4_root / "page_photos"
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_png in output_dir.glob("*.png"):
        old_png.unlink()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("Segoe UI", 10))
    qss_path = paths.phase4_root / "app" / "resources" / "app_styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    window = MainWindow(paths)
    window.resize(1440, 920)
    window.show()
    for _ in range(8):
        app.processEvents()
        time.sleep(0.05)
    def wait_for_sensor_refresh(widget) -> None:
        if hasattr(widget, "refresh_all"):
            try:
                widget.refresh_all()
                for _ in range(120):
                    app.processEvents()
                    time.sleep(0.05)
                    if not getattr(widget, "refresh_busy", False):
                        break
            except Exception:
                pass

    tabs = window.tabs
    written: list[str] = []
    for index, filename, power_source, view_method, scroll_value in PHOTO_PLAN:
        tabs.setCurrentIndex(index)
        for _ in range(8):
            app.processEvents()
            time.sleep(0.05)
        current = tabs.currentWidget()
        if power_source and hasattr(current, "power_source_box"):
            current.power_source_box.setCurrentText(power_source)
            for _ in range(8):
                app.processEvents()
                time.sleep(0.05)
        if view_method and hasattr(current, view_method):
            getattr(current, view_method)()
        if index == 3:
            wait_for_sensor_refresh(current)
            if view_method and hasattr(current, view_method):
                getattr(current, view_method)()
            scroll_area = current.findChild(QScrollArea)
            if scroll_area is not None:
                scroll_area.verticalScrollBar().setValue(scroll_value)
            for _ in range(8):
                app.processEvents()
                time.sleep(0.05)
        close_popups(window, app)
        path = output_dir / filename
        pixmap = window.grab()
        if not pixmap.save(str(path), "PNG"):
            raise RuntimeError(f"Failed to save screenshot: {path}")
        written.append(str(path))

    readme = output_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# AeroTune Phase 8 Page Photos",
                "",
                "- 01_dashboard.png: dashboard with telemetry readiness, CPU provider health, and safe apply gate status.",
                "- 02_cpu_presets_ac.png: CPU Presets page in AC power-source view.",
                "- 03_cpu_presets_dc.png: CPU Presets page in DC power-source view.",
                "- 04_gpu_profiles.png: GPU Profiles page with MSI profile launch still blocked.",
                "- 05_sensors_overview_refined.png: refined Sensors overview with hero telemetry strip and status pills.",
                "- 06_sensors_cpu_partial_provider.png: CPU panel showing valid load/voltage and unavailable/stale temperature/power/clock.",
                "- 07_sensors_gpu_panels.png: GPU-oriented hardware panel region with NVIDIA/LHM GPU classification.",
                "- 08_sensors_all_raw_validity.png: all raw sensor explorer with validity, validity reason, provider, and subcategory columns.",
                "- 09_sensors_cpu_diagnostics.png: CPU provider diagnostics, stale-zero rows, invalid rows, and raw CPU sensors.",
                "- 10_game_automation.png: Game Automation page with read-only command-line matching.",
                "- 11_auto_tuning.png: planned Auto Tuning workflow, disabled for Phase 8.",
                "- 12_fan_experimental.png: fan/GCC research page, write paths blocked.",
                "- 13_logs.png: logs and diagnostic-bundle page.",
                "- 14_settings.png: safety, gate, risk, sensor config, provider status, and power-plan management page.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("\n".join(written))
    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
