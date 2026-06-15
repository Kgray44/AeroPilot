from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget, QWidget

from app.ui.common import add_form_row, fill_table, make_card, make_metric, make_page_header, make_scroll_page


class TelemetryTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.refresh_all)
        layout, _body = make_scroll_page(self)
        layout.addWidget(
            make_page_header(
                "Sensors / Telemetry",
                "Live read-only readings from NVIDIA, PresentMon, and LibreHardwareMonitor. PresentMon capture starts only when you press Start.",
                [("Read-only", "safe"), ("Capture opt-in", "neutral")],
            )
        )

        self.metric_row = QHBoxLayout()
        metric_panel = QWidget()
        metric_panel.setLayout(self.metric_row)
        layout.addWidget(metric_panel)

        nvidia_card, nvidia_layout = make_card("NVIDIA GPU readings", "Read live through nvidia-smi.")
        nvidia_card.setObjectName("nvidia_readings_panel")
        self.nvidia_table = QTableWidget()
        nvidia_layout.addWidget(self.nvidia_table)
        layout.addWidget(nvidia_card)

        pm_card, pm_layout = make_card("PresentMon frame readings", "Start an opt-in capture to read FPS and frame-time from CSV output.")
        pm_card.setObjectName("presentmon_readings_panel")
        self.presentmon_candidate = QComboBox()
        self.presentmon_candidate.addItems([row.get("path", "") for row in self.window.presentmon.candidates()])
        self.presentmon_process = QLineEdit()
        self.presentmon_process.setPlaceholderText("Optional process name, e.g. BF6.exe")
        self.presentmon_duration = QSpinBox()
        self.presentmon_duration.setRange(1, 600)
        self.presentmon_duration.setValue(60)
        add_form_row(pm_layout, "Candidate", self.presentmon_candidate)
        add_form_row(pm_layout, "Process filter", self.presentmon_process)
        add_form_row(pm_layout, "Capture seconds", self.presentmon_duration)
        pm_buttons = QHBoxLayout()
        start_pm = QPushButton("Start PresentMon Capture")
        start_pm.clicked.connect(self.start_presentmon)
        stop_pm = QPushButton("Stop PresentMon")
        stop_pm.clicked.connect(self.stop_presentmon)
        refresh_pm = QPushButton("Refresh Frame Reading")
        refresh_pm.clicked.connect(self.refresh_presentmon)
        pm_buttons.addWidget(start_pm)
        pm_buttons.addWidget(stop_pm)
        pm_buttons.addWidget(refresh_pm)
        pm_buttons.addStretch(1)
        pm_layout.addLayout(pm_buttons)
        self.presentmon_table = QTableWidget()
        pm_layout.addWidget(self.presentmon_table)
        layout.addWidget(pm_card)

        lhm_card, lhm_layout = make_card("LibreHardwareMonitor readings", "Loads the discovered DLL through a read-only PowerShell probe and displays available sensors.")
        lhm_card.setObjectName("librehardwaremonitor_readings_panel")
        lhm_buttons = QHBoxLayout()
        refresh_lhm = QPushButton("Refresh LHM Sensors")
        refresh_lhm.clicked.connect(self.refresh_lhm)
        lhm_buttons.addWidget(refresh_lhm)
        lhm_buttons.addStretch(1)
        lhm_layout.addLayout(lhm_buttons)
        self.lhm_table = QTableWidget()
        lhm_layout.addWidget(self.lhm_table)
        layout.addWidget(lhm_card)

        polling_card, polling_layout = make_card("Polling", "Save app-side telemetry preferences.")
        self.poll_enabled = QCheckBox("Enable live polling in app")
        self.poll_interval = QSpinBox()
        self.poll_interval.setRange(3, 60)
        self.poll_interval.setValue(int(self.surface.app_config.get("polling", {}).get("interval_seconds", 3)))
        self.log_snapshots = QCheckBox("Log telemetry snapshots")
        self.log_snapshots.setChecked(bool(self.surface.app_config.get("polling", {}).get("log_telemetry_snapshots", False)))
        self.poll_enabled.setChecked(bool(self.surface.app_config.get("polling", {}).get("enabled", False)))
        save_polling = QPushButton("Save Polling Settings JSON")
        save_polling.clicked.connect(self.save_polling)
        polling_layout.addWidget(self.poll_enabled)
        add_form_row(polling_layout, "Interval seconds", self.poll_interval)
        polling_layout.addWidget(self.log_snapshots)
        polling_layout.addWidget(save_polling)
        layout.addWidget(polling_card)
        layout.addStretch(1)
        self.refresh_all()

    def _set_metrics(self, values: list[tuple[str, str, str]]) -> None:
        while self.metric_row.count():
            item = self.metric_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for label, value, tone in values:
            self.metric_row.addWidget(make_metric(label, value, tone))
        self.metric_row.addStretch(1)

    def refresh_all(self) -> None:
        nvidia = self.refresh_nvidia()
        pm = self.refresh_presentmon()
        lhm_headline = self.window.lhm.headline(getattr(self, "_last_lhm_snapshot", None)) if hasattr(self, "_last_lhm_snapshot") else {"CPU": "Refresh LHM", "Fan": "Fan n/a", "Sensors": "not read"}
        cpu_headline = lhm_headline.get("CPU", "n/a")
        if cpu_headline == "CPU temp n/a":
            cpu_headline = lhm_headline.get("Sensors", cpu_headline)
        gpu_data = nvidia.get("data", {}) if nvidia.get("ok") else {}
        self._set_metrics(
            [
                ("GPU temp", f"{gpu_data.get('temperature.gpu', 'n/a')} C", "neutral"),
                ("GPU util", f"{gpu_data.get('utilization.gpu', 'n/a')}%", "neutral"),
                ("GPU power", f"{gpu_data.get('power.draw', 'n/a')} W", "neutral"),
                ("FPS", f"{pm.get('fps_average_sample', 'idle')}", "safe" if pm.get("ok") else "warn"),
                ("CPU", cpu_headline, "neutral"),
            ]
        )

    def refresh_nvidia(self) -> dict:
        result = self.window.nvidia.telemetry_snapshot()
        data = result.get("data", {}) if result.get("ok") else {"error": result.get("error") or result.get("stderr")}
        fill_table(self.nvidia_table, ["Field", "Value"], [[key, value] for key, value in data.items()])
        return result

    def start_presentmon(self) -> None:
        process_name = self.presentmon_process.text().strip() or None
        candidate = self.presentmon_candidate.currentText() or None
        result = self.window.presentmon.start_capture(process_name=process_name, duration_seconds=int(self.presentmon_duration.value()), candidate_path=candidate)
        if not result.get("ok"):
            QMessageBox.warning(self, "PresentMon start failed", str(result.get("error")))
        self.refresh_presentmon()

    def stop_presentmon(self) -> None:
        self.window.presentmon.stop_capture()
        self.refresh_presentmon()

    def refresh_presentmon(self) -> dict:
        result = self.window.presentmon.latest_reading()
        fill_table(self.presentmon_table, ["Field", "Value"], [[key, value] for key, value in result.items() if key != "command"])
        return result

    def refresh_lhm(self) -> dict:
        result = self.window.lhm.sensor_snapshot()
        self._last_lhm_snapshot = result
        if not result.get("ok"):
            fill_table(self.lhm_table, ["Field", "Value"], [["error", result.get("error")], ["source", result.get("source")]])
            return result
        rows = result.get("sensors", [])
        fill_table(
            self.lhm_table,
            ["Hardware", "Type", "Sensor", "Value", "Min", "Max"],
            [[row.get("hardware"), row.get("sensor_type"), row.get("name"), row.get("value"), row.get("min"), row.get("max")] for row in rows],
        )
        self.refresh_all()
        return result

    def save_polling(self) -> None:
        polling = self.surface.app_config.setdefault("polling", {})
        polling["enabled"] = self.poll_enabled.isChecked()
        polling["interval_seconds"] = int(self.poll_interval.value())
        polling["log_telemetry_snapshots"] = self.log_snapshots.isChecked()
        path = self.surface.save_app_config()
        QMessageBox.information(self, "Polling settings saved", f"Saved app-side config only:\n{path}")
