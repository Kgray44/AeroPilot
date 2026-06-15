from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSpinBox, QTableWidget, QVBoxLayout, QWidget

from app.ui.common import fill_controls_table, fill_table


class TelemetryTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.refresh_nvidia)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Live telemetry is read-only. PresentMon capture and LibreHardwareMonitor DLL loading are not used in Phase 3."))

        layout.addWidget(QLabel("Live NVIDIA telemetry"))
        self.nvidia_table = QTableWidget()
        layout.addWidget(self.nvidia_table, 1)
        self.last_refresh = QLabel("")
        layout.addWidget(self.last_refresh)

        buttons = QHBoxLayout()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_nvidia)
        start = QPushButton("Start Polling")
        start.clicked.connect(self.start_polling)
        stop = QPushButton("Stop Polling")
        stop.clicked.connect(self.timer.stop)
        buttons.addWidget(refresh)
        buttons.addWidget(start)
        buttons.addWidget(stop)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        layout.addWidget(QLabel("Telemetry field catalog"))
        self.catalog_table = QTableWidget()
        layout.addWidget(self.catalog_table, 1)
        fill_controls_table(self.catalog_table, [c for c in self.surface.by_tab("Sensors / Telemetry") if c.get("category") in {"GPU power/clock telemetry", "FPS/frame capture", "CPU power behavior"}])

        settings = QGridLayout()
        self.poll_enabled = QCheckBox("Enable live polling in app")
        self.poll_interval = QSpinBox()
        self.poll_interval.setRange(2, 60)
        self.poll_interval.setValue(int(self.surface.app_config.get("polling", {}).get("interval_seconds", 2)))
        self.log_snapshots = QCheckBox("Log telemetry snapshots")
        self.log_snapshots.setChecked(bool(self.surface.app_config.get("polling", {}).get("log_telemetry_snapshots", False)))
        self.poll_enabled.setChecked(bool(self.surface.app_config.get("polling", {}).get("enabled", False)))
        save_polling = QPushButton("Save Polling Settings JSON")
        save_polling.clicked.connect(self.save_polling)
        settings.addWidget(self.poll_enabled, 0, 0)
        settings.addWidget(QLabel("Interval seconds"), 0, 1)
        settings.addWidget(self.poll_interval, 0, 2)
        settings.addWidget(self.log_snapshots, 1, 0)
        settings.addWidget(save_polling, 1, 2)
        layout.addLayout(settings)

        layout.addWidget(QLabel("PresentMon candidates"))
        self.presentmon_box = QComboBox()
        self.presentmon_box.addItems([row.get("path", "") for row in self.window.presentmon.candidates()])
        preferred = self.surface.app_config.get("presentmon", {}).get("preferred_candidate")
        if preferred:
            idx = self.presentmon_box.findText(preferred)
            if idx >= 0:
                self.presentmon_box.setCurrentIndex(idx)
        save_candidate = QPushButton("Save Preferred Candidate JSON")
        save_candidate.clicked.connect(self.save_presentmon_candidate)
        candidate_row = QHBoxLayout()
        candidate_row.addWidget(self.presentmon_box, 1)
        candidate_row.addWidget(save_candidate)
        layout.addLayout(candidate_row)

        self.presentmon_table = QTableWidget()
        layout.addWidget(self.presentmon_table, 1)
        fill_table(
            self.presentmon_table,
            ["Path", "Version", "Last modified", "Score note"],
            [[c.get("path"), c.get("file_version"), c.get("last_write_local"), "candidate only; no capture"] for c in self.window.presentmon.candidates()],
        )

        layout.addWidget(QLabel("LibreHardwareMonitor future section"))
        self.lhm_table = QTableWidget()
        layout.addWidget(self.lhm_table, 1)
        lhm = self.window.lhm.status()
        fill_table(self.lhm_table, ["Path", "Version", "Status"], [[row.get("path"), row.get("file_version"), "future optional library"] for row in lhm.get("library_paths", [])])
        self.refresh_nvidia()

    def refresh_nvidia(self) -> None:
        result = self.window.nvidia.telemetry_snapshot()
        data = result.get("data", {}) if result.get("ok") else {"error": result.get("error") or result.get("stderr")}
        fill_table(self.nvidia_table, ["Field", "Value"], [[key, value] for key, value in data.items()])
        self.last_refresh.setText(f"Last refresh source: {'live nvidia-smi' if result.get('ok') else 'fallback/error'}")

    def start_polling(self) -> None:
        self.timer.setInterval(max(2, int(self.poll_interval.value())) * 1000)
        self.timer.start()

    def save_polling(self) -> None:
        polling = self.surface.app_config.setdefault("polling", {})
        polling["enabled"] = self.poll_enabled.isChecked()
        polling["interval_seconds"] = int(self.poll_interval.value())
        polling["log_telemetry_snapshots"] = self.log_snapshots.isChecked()
        path = self.surface.save_app_config()
        QMessageBox.information(self, "Polling settings saved", f"Saved app-side config only:\n{path}")

    def save_presentmon_candidate(self) -> None:
        presentmon = self.surface.app_config.setdefault("presentmon", {})
        presentmon["preferred_candidate"] = self.presentmon_box.currentText()
        presentmon["candidate_selection_note"] = "Phase 3 preference only. No capture was started."
        path = self.surface.save_app_config()
        QMessageBox.information(self, "PresentMon preference saved", f"Saved app-side config only:\n{path}")
