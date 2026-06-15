from __future__ import annotations

import os
import time
from collections import Counter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QPlainTextEdit, QWidget

from app.core.config_loader import save_json_inside_phase4
from app.core.state_snapshot import collect_snapshot
from app.ui.common import horizontal_cards, make_badge, make_card, make_metric, make_page_header, make_scroll_page


class DashboardTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.labels: dict[str, QLabel] = {}
        self.last_snapshot: dict | None = None

        layout, _body = make_scroll_page(self)
        layout.addWidget(
            make_page_header(
                "AeroTune",
                "Read-only telemetry, backup status, and dry-run control previews for the AERO X16 optimization workflow.",
                [("READ-ONLY / DRY-RUN", "safe"), ("Phase 4 Backup / Sandbox", "neutral")],
            )
        )

        self.metric_row = QHBoxLayout()
        self.metric_row.setSpacing(12)
        metric_panel = QWidget()
        metric_panel.setLayout(self.metric_row)
        layout.addWidget(metric_panel)

        status_card, status_layout = make_card("System status", "Current availability and guardrail state.")
        self.status_grid = QGridLayout()
        self.status_grid.setHorizontalSpacing(24)
        self.status_grid.setVerticalSpacing(10)
        status_layout.addLayout(self.status_grid)
        layout.addWidget(status_card)

        phase_card, phase_layout = make_card("Backup and apply gates", "Phase 4 proves infrastructure without enabling real apply actions.")
        self.phase_grid = QGridLayout()
        self.phase_grid.setHorizontalSpacing(24)
        self.phase_grid.setVerticalSpacing(10)
        phase_layout.addLayout(self.phase_grid)
        layout.addWidget(phase_card)

        snapshot_card, snapshot_layout = make_card("Read-only snapshot", "Live/fallback telemetry in a compact diagnostic view.")
        self.telemetry = QPlainTextEdit()
        self.telemetry.setReadOnly(True)
        self.telemetry.setMinimumHeight(220)
        snapshot_layout.addWidget(self.telemetry)
        layout.addWidget(snapshot_card)

        buttons = QHBoxLayout()
        for text, callback in [
            ("Refresh Snapshot", self.refresh_snapshot),
            ("Export Dashboard Snapshot", self.export_snapshot),
            ("Open Phase 1 Report", lambda: self.open_path(self.window.paths.phase1_root / "phase1_exploration_report.md")),
            ("Open Logs Folder", lambda: self.open_path(self.window.paths.logs_dir)),
        ]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addStretch(1)
        self.refresh_snapshot()

    def _set_grid_rows(self, grid: QGridLayout, rows: list[tuple[str, str]]) -> None:
        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for row, (label, value) in enumerate(rows):
            key = QLabel(label)
            key.setObjectName("form_label")
            val = QLabel(value)
            val.setWordWrap(True)
            val.setTextInteractionFlags(val.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(key, row, 0)
            grid.addWidget(val, row, 1)

    def _refresh_metrics(self, metrics: list[QWidget]) -> None:
        while self.metric_row.count():
            item = self.metric_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for metric in metrics:
            self.metric_row.addWidget(metric)
        self.metric_row.addStretch(1)

    def refresh_snapshot(self) -> None:
        surface = self.window.control_surface
        controls = surface.controls
        summary = self.window.phase1.summary()
        status_counts = Counter(row.get("status") for row in controls)
        snapshot = collect_snapshot(self.window.paths)
        self.last_snapshot = snapshot

        phase4 = snapshot.get("phase4", {})
        backup = phase4.get("backup_manifest", {})
        restore = phase4.get("restore_manifest", {})
        sandbox = phase4.get("sandbox_result", {})
        gates = phase4.get("apply_gates", {})
        matched = snapshot.get("process_targets", {}).get("matched_targets", [])

        backup_ready = bool(backup.get("backup_sufficient_for_phase5_apply_tests", False))
        sandbox_passed = bool(sandbox.get("passed", False))
        power_exported = bool(gates.get("active_power_plan_exported", False))

        self._refresh_metrics(
            [
                make_metric("Controls mapped", str(len(controls))),
                make_metric("Readable CPU settings", str(summary.get("readable_cpu_settings"))),
                make_metric("Running targets", str(len(matched))),
                make_metric("Sandbox apply test", "Passed" if sandbox_passed else "Not passed", "safe" if sandbox_passed else "warn"),
                make_metric("Phase 5 ready", "No" if not backup_ready else "Yes", "warn" if not backup_ready else "safe"),
            ]
        )

        self._set_grid_rows(
            self.status_grid,
            [
                ("App", "AeroTune 0.4.0-preview"),
                ("Safety mode", "READ-ONLY / DRY-RUN"),
                ("Active power plan", str(snapshot.get("active_power_plan", {}).get("name") or summary.get("active_power_plan"))),
                ("MSI Afterburner", str(summary.get("msi_afterburner_detected"))),
                ("nvidia-smi", str(summary.get("nvidia_smi_detected"))),
                ("PresentMon", str(summary.get("presentmon_detected"))),
                ("LibreHardwareMonitor", str(summary.get("librehardwaremonitor_detected"))),
                ("Gigabyte/GCC", str(summary.get("gigabyte_detected"))),
                ("Dry-run preview controls", str(sum(1 for row in controls if row.get("coverage", {}).get("has_dryrun_preview")))),
                ("Blocked/future controls", str(status_counts.get("blocked", 0) + status_counts.get("future", 0) + status_counts.get("blocked_or_unavailable", 0))),
            ],
        )

        before = sandbox.get("active_scheme_before", {}).get("guid")
        after = sandbox.get("active_scheme_after", {}).get("guid")
        self._set_grid_rows(
            self.phase_grid,
            [
                ("Backup manifest", "present" if backup else "missing"),
                ("Restore manifest", "present" if restore else "missing"),
                ("Last backup timestamp", str(backup.get("generated_local", "not generated"))),
                ("Power plan export", "usable" if power_exported else "blocked or missing"),
                ("Sandbox apply test", "passed" if sandbox_passed else "not run or failed"),
                ("Active plan before/after", "match" if before and before == after else "not verified"),
                ("MSI backup", str(gates.get("msi_configs_backed_up", False))),
                ("Active-plan writes", str(gates.get("active_plan_write_enabled", False))),
                ("MSI profile apply", str(gates.get("msi_profile_apply_enabled", False))),
            ],
        )

        self.telemetry.setPlainText(str({"nvidia_smi": snapshot.get("nvidia_smi"), "process_targets": snapshot.get("process_targets"), "phase4": phase4}))

    def export_snapshot(self) -> None:
        snapshot = self.last_snapshot or collect_snapshot(self.window.paths)
        target = self.window.paths.raw_outputs_dir / f"dashboard_snapshot_{time.strftime('%Y%m%d-%H%M%S')}.json"
        save_json_inside_phase4(target, snapshot, self.window.paths)
        QMessageBox.information(self, "Snapshot exported", str(target))

    def open_path(self, path) -> None:
        try:
            os.startfile(path)
        except Exception as exc:
            QMessageBox.warning(self, "Open failed", str(exc))
