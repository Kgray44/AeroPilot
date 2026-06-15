from __future__ import annotations

import os
import time
import zipfile

from PySide6.QtWidgets import QHBoxLayout, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget


class LogsTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)
        buttons = QHBoxLayout()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        open_logs = QPushButton("Open logs folder")
        open_logs.clicked.connect(lambda: os.startfile(self.window.paths.logs_dir))
        bundle = QPushButton("Export app diagnostic bundle")
        bundle.clicked.connect(self.export_bundle)
        buttons.addWidget(refresh)
        buttons.addWidget(open_logs)
        buttons.addWidget(bundle)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        for folder in [self.window.paths.logs_dir, self.window.paths.raw_outputs_dir]:
            for path in sorted(folder.glob("*")):
                if path.is_file():
                    self.list_widget.addItem(str(path))

    def export_bundle(self) -> None:
        target = self.window.paths.logs_dir / f"phase3_diagnostic_bundle_{time.strftime('%Y%m%d-%H%M%S')}.zip"
        root = self.window.paths.phase3_root.resolve()
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in root.rglob("*"):
                if path.is_file() and path.resolve() != target.resolve():
                    archive.write(path, path.relative_to(root))
        QMessageBox.information(self, "Bundle exported", str(target))
        self.refresh()
