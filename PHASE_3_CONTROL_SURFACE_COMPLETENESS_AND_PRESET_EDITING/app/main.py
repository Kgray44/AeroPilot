from __future__ import annotations

import sys

from app import APP_NAME
from app.core.app_paths import AppPaths
from app.core.logging_setup import configure_logging


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("PySide6 is not installed. Install it in a local environment with: pip install -r requirements.txt")
        return 2

    from app.ui.main_window import MainWindow

    paths = AppPaths.discover()
    paths.ensure_phase2_dirs()
    configure_logging(paths.logs_dir)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    qss_path = paths.phase2_root / "app" / "resources" / "app_styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    window = MainWindow(paths)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
