from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QComboBox

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
    (0, "01_dashboard.png", None),
    (1, "02_cpu_presets_ac.png", "AC"),
    (1, "03_cpu_presets_dc.png", "DC"),
    (2, "04_gpu_profiles.png", None),
    (3, "05_sensors.png", None),
    (4, "06_game_automation.png", None),
    (5, "07_auto_tuning.png", None),
    (6, "08_fan_experimental.png", None),
    (7, "09_logs.png", None),
    (8, "10_settings.png", None),
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
    try:
        lhm_snapshot = window.lhm.sensor_snapshot()
        window._apply_lhm_headline(window.lhm.headline(lhm_snapshot) | {"ok": bool(lhm_snapshot.get("ok")), "error": lhm_snapshot.get("error")})
    except Exception:
        pass

    tabs = window.tabs
    written: list[str] = []
    for index, filename, power_source in PHOTO_PLAN:
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
        if hasattr(current, "refresh_lhm"):
            try:
                current.refresh_lhm()
                for _ in range(4):
                    app.processEvents()
                    time.sleep(0.05)
            except Exception:
                pass
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
                "# AeroTune Phase 5 Page Photos",
                "",
                "- 01_dashboard.png: dashboard with Phase 5 backup/export/apply gate status.",
                "- 02_cpu_presets_ac.png: CPU Presets page in AC power-source view.",
                "- 03_cpu_presets_dc.png: CPU Presets page in DC power-source view.",
                "- 04_gpu_profiles.png: GPU Profiles page with MSI profile launch still blocked.",
                "- 05_sensors.png: Sensors page with NVIDIA, PresentMon, and LibreHardwareMonitor sections.",
                "- 06_game_automation.png: Game Automation page with read-only command-line matching.",
                "- 07_auto_tuning.png: planned Auto Tuning workflow, disabled for Phase 5.",
                "- 08_fan_experimental.png: fan/GCC research page, write paths blocked.",
                "- 09_logs.png: logs and diagnostic-bundle page.",
                "- 10_settings.png: safety, gate, risk, and power-plan management page.",
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
