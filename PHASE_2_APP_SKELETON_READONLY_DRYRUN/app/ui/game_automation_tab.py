from __future__ import annotations

import time

from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QPushButton, QTableWidget, QVBoxLayout, QWidget

from app.core.config_loader import save_json_inside_phase2
from app.ui.common import fill_table


class GameAutomationTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table, 1)
        buttons = QHBoxLayout()
        refresh = QPushButton("Refresh Running Processes")
        refresh.clicked.connect(self.refresh)
        preview = QPushButton("Preview Rule Match")
        preview.clicked.connect(self.preview_rule)
        export = QPushButton("Export Process Snapshot")
        export.clicked.connect(self.export_snapshot)
        buttons.addWidget(refresh)
        buttons.addWidget(preview)
        buttons.addWidget(export)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        self.rows = self.window.processes.match_targets()
        fill_table(
            self.table,
            ["Target ID", "Friendly", "Category", "Configured process names", "Running now", "Matched processes", "Automation enabled"],
            [
                [
                    row.get("id"),
                    row.get("friendly"),
                    row.get("category"),
                    ", ".join(row.get("process_names", [])),
                    row.get("running_now"),
                    ", ".join([str(proc.get("ProcessName")) for proc in row.get("matched_processes", [])]),
                    row.get("automation_enabled"),
                ]
                for row in self.rows
            ],
        )

    def preview_rule(self) -> None:
        current = self.table.currentRow()
        if current < 0 or current >= len(getattr(self, "rows", [])):
            QMessageBox.information(self, "No rule selected", "Select a rule first.")
            return
        QMessageBox.information(self, "Preview only", str(self.rows[current]) + "\n\nNo presets are applied in Phase 2.")

    def export_snapshot(self) -> None:
        target = self.window.paths.raw_outputs_dir / f"process_snapshot_{time.strftime('%Y%m%d-%H%M%S')}.json"
        save_json_inside_phase2(target, {"targets": getattr(self, "rows", [])}, self.window.paths)
        QMessageBox.information(self, "Exported", str(target))
