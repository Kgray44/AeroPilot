from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTableWidget, QVBoxLayout, QWidget

from app.ui.common import fill_table


class TelemetryTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.refresh)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Read-only NVIDIA telemetry. Polling interval is 2 seconds."))
        self.table = QTableWidget()
        layout.addWidget(self.table, 1)

        self.lhm_status = QLabel(str(self.window.lhm.status()))
        layout.addWidget(QLabel("LibreHardwareMonitor future integration status"))
        layout.addWidget(self.lhm_status)

        buttons = QHBoxLayout()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        start = QPushButton("Start Polling")
        start.clicked.connect(self.timer.start)
        stop = QPushButton("Stop Polling")
        stop.clicked.connect(self.timer.stop)
        buttons.addWidget(refresh)
        buttons.addWidget(start)
        buttons.addWidget(stop)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        result = self.window.nvidia.telemetry_snapshot()
        data = result.get("data", {}) if result.get("ok") else {"error": result.get("error")}
        fill_table(self.table, ["Field", "Value"], [[key, value] for key, value in data.items()])
