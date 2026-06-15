from __future__ import annotations

import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app import APP_NAME
from app.core.app_paths import AppPaths
from app.ui.main_window import MainWindow


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return slug or "page"


def main() -> int:
    paths = AppPaths.discover()
    output_dir = paths.phase4_root / "page_photos"
    output_dir.mkdir(parents=True, exist_ok=True)

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
    for index in range(tabs.count()):
        tabs.setCurrentIndex(index)
        for _ in range(8):
            app.processEvents()
            time.sleep(0.05)
        name = tabs.tabText(index)
        current = tabs.currentWidget()
        if hasattr(current, "refresh_lhm"):
            try:
                current.refresh_lhm()
                for _ in range(4):
                    app.processEvents()
                    time.sleep(0.05)
            except Exception:
                pass
        path = output_dir / f"{index + 1:02d}_{slugify(name)}.png"
        pixmap = window.grab()
        if not pixmap.save(str(path), "PNG"):
            raise RuntimeError(f"Failed to save screenshot: {path}")
        written.append(str(path))

    print("\n".join(written))
    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
