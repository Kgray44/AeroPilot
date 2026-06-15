from __future__ import annotations

import os
import time
from collections import Counter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget

from app.core.config_loader import save_json_inside_phase3
from app.core.state_snapshot import collect_snapshot
from app.ui.common import make_badge


class DashboardTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.labels: dict[str, QLabel] = {}
        self.last_snapshot: dict | None = None

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(make_badge("AERO X16 Control Center", "strong"))
        header.addWidget(make_badge("READ-ONLY / DRY-RUN", "safe"))
        header.addWidget(make_badge("Phase 3 Control Surface", "neutral"))
        header.addStretch(1)
        layout.addLayout(header)

        grid = QGridLayout()
        layout.addLayout(grid)
        labels = [
            "App version / phase",
            "Safety mode",
            "Active power plan",
            "MSI Afterburner detected",
            "nvidia-smi detected",
            "PresentMon detected",
            "LibreHardwareMonitor detected",
            "Gigabyte/GCC detected",
            "Manifest controls",
            "Editable controls",
            "Dry-run preview controls",
            "Blocked/future controls",
            "Readable CPU settings",
            "Running target process summary",
        ]
        for row, label in enumerate(labels):
            grid.addWidget(QLabel(label), row, 0)
            value = QLabel("")
            value.setTextInteractionFlags(value.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse)
            self.labels[label] = value
            grid.addWidget(value, row, 1)

        self.telemetry = QPlainTextEdit()
        self.telemetry.setReadOnly(True)
        layout.addWidget(QLabel("Current read-only snapshot"))
        layout.addWidget(self.telemetry, 1)

        buttons = QHBoxLayout()
        for text, callback in [
            ("Refresh Read-only Snapshot", self.refresh_snapshot),
            ("Export Current Dashboard Snapshot", self.export_snapshot),
            ("Open Phase 1 Report", lambda: self.open_path(self.window.paths.phase1_root / "phase1_exploration_report.md")),
            ("Open Phase 3 Logs Folder", lambda: self.open_path(self.window.paths.logs_dir)),
        ]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.refresh_snapshot()

    def refresh_snapshot(self) -> None:
        surface = self.window.control_surface
        controls = surface.controls
        summary = self.window.phase1.summary()
        status_counts = Counter(row.get("status") for row in controls)
        snapshot = collect_snapshot(self.window.paths)
        self.last_snapshot = snapshot

        self.labels["App version / phase"].setText("0.3.0-preview / PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING")
        self.labels["Safety mode"].setText("READ-ONLY / DRY-RUN")
        self.labels["Active power plan"].setText(str(snapshot.get("active_power_plan", {}).get("name") or summary.get("active_power_plan")))
        self.labels["MSI Afterburner detected"].setText(str(summary.get("msi_afterburner_detected")))
        self.labels["nvidia-smi detected"].setText(str(summary.get("nvidia_smi_detected")))
        self.labels["PresentMon detected"].setText(str(summary.get("presentmon_detected")))
        self.labels["LibreHardwareMonitor detected"].setText(str(summary.get("librehardwaremonitor_detected")))
        self.labels["Gigabyte/GCC detected"].setText(str(summary.get("gigabyte_detected")))
        self.labels["Manifest controls"].setText(str(len(controls)))
        self.labels["Editable controls"].setText(str(sum(1 for row in controls if row.get("desired_value_editing", {}).get("editable_in_phase3"))))
        self.labels["Dry-run preview controls"].setText(str(sum(1 for row in controls if row.get("coverage", {}).get("has_dryrun_preview"))))
        self.labels["Blocked/future controls"].setText(str(status_counts.get("blocked", 0) + status_counts.get("future", 0) + status_counts.get("blocked_or_unavailable", 0)))
        self.labels["Readable CPU settings"].setText(str(summary.get("readable_cpu_settings")))
        matched = snapshot.get("process_targets", {}).get("matched_targets", [])
        self.labels["Running target process summary"].setText(f"{len(matched)} matched target processes")
        self.telemetry.setPlainText(str({"nvidia_smi": snapshot.get("nvidia_smi"), "process_targets": snapshot.get("process_targets")}))

    def export_snapshot(self) -> None:
        snapshot = self.last_snapshot or collect_snapshot(self.window.paths)
        target = self.window.paths.raw_outputs_dir / f"dashboard_snapshot_{time.strftime('%Y%m%d-%H%M%S')}.json"
        save_json_inside_phase3(target, snapshot, self.window.paths)
        QMessageBox.information(self, "Snapshot exported", str(target))

    def open_path(self, path) -> None:
        try:
            os.startfile(path)
        except Exception as exc:
            QMessageBox.warning(self, "Open failed", str(exc))
