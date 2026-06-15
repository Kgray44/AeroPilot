from __future__ import annotations

import time

from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.config_loader import save_json_inside_phase2
from app.core.state_snapshot import collect_snapshot
from app.ui.common import make_badge


class DashboardTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.summary_labels: dict[str, QLabel] = {}
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(make_badge("AERO X16 Control Center", "strong"))
        header.addWidget(make_badge("READ-ONLY / DRY-RUN", "safe"))
        header.addStretch(1)
        layout.addLayout(header)

        grid = QGridLayout()
        layout.addLayout(grid)
        for row, label in enumerate(
            [
                "App version / phase",
                "Active power plan",
                "MSI Afterburner detected",
                "nvidia-smi detected",
                "PresentMon detected",
                "LibreHardwareMonitor detected",
                "Gigabyte/GCC detected",
                "Risk catalog items",
                "Readable CPU settings",
                "Running target process summary",
            ]
        ):
            grid.addWidget(QLabel(label), row, 0)
            value = QLabel("")
            value.setTextInteractionFlags(value.textInteractionFlags() | value.textInteractionFlags().TextSelectableByMouse)
            self.summary_labels[label] = value
            grid.addWidget(value, row, 1)

        self.telemetry = QPlainTextEdit()
        self.telemetry.setReadOnly(True)
        self.telemetry.setMaximumBlockCount(200)
        layout.addWidget(QLabel("Current GPU telemetry snapshot"))
        layout.addWidget(self.telemetry, 1)

        buttons = QHBoxLayout()
        refresh = QPushButton("Refresh Read-only Snapshot")
        refresh.clicked.connect(self.refresh_snapshot)
        export = QPushButton("Export Current Dashboard Snapshot")
        export.clicked.connect(self.export_snapshot)
        open_report = QPushButton("Open Phase 1 Report")
        open_report.clicked.connect(self.open_phase1_report)
        open_logs = QPushButton("Open Phase 2 Logs Folder")
        open_logs.clicked.connect(lambda: self.open_path(self.window.paths.logs_dir))
        for button in (refresh, export, open_report, open_logs):
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.refresh_snapshot()

    def refresh_snapshot(self) -> None:
        snapshot = collect_snapshot(self.window.paths)
        summary = self.window.phase1.summary()
        self.summary_labels["App version / phase"].setText("0.2.0-preview / PHASE_2_APP_SKELETON_READONLY_DRYRUN")
        self.summary_labels["Active power plan"].setText(str(summary.get("active_power_plan")))
        self.summary_labels["MSI Afterburner detected"].setText(str(summary.get("msi_afterburner_detected")))
        self.summary_labels["nvidia-smi detected"].setText(str(summary.get("nvidia_smi_detected")))
        self.summary_labels["PresentMon detected"].setText(str(summary.get("presentmon_detected")))
        self.summary_labels["LibreHardwareMonitor detected"].setText(str(summary.get("librehardwaremonitor_detected")))
        self.summary_labels["Gigabyte/GCC detected"].setText(str(summary.get("gigabyte_detected")))
        self.summary_labels["Risk catalog items"].setText(str(summary.get("risk_item_count")))
        self.summary_labels["Readable CPU settings"].setText(str(summary.get("readable_cpu_settings")))
        matches = [row for row in snapshot.get("process_targets", []) if row.get("running_now")]
        self.summary_labels["Running target process summary"].setText(f"{len(matches)} matched targets running now")
        self.telemetry.setPlainText(str(snapshot.get("nvidia_smi", {})))
        self.last_snapshot = snapshot

    def export_snapshot(self) -> None:
        snapshot = getattr(self, "last_snapshot", None) or collect_snapshot(self.window.paths)
        target = self.window.paths.raw_outputs_dir / f"dashboard_snapshot_{time.strftime('%Y%m%d-%H%M%S')}.json"
        save_json_inside_phase2(target, snapshot, self.window.paths)
        QMessageBox.information(self, "Snapshot exported", str(target))

    def open_phase1_report(self) -> None:
        self.open_path(self.window.paths.phase1_root / "phase1_exploration_report.md")

    def open_path(self, path) -> None:
        try:
            import os

            os.startfile(path)
        except Exception as exc:
            QMessageBox.warning(self, "Open failed", str(exc))
