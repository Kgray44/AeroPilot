from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from app.core.config_loader import save_json_inside_phase3
from app.ui.common import fill_controls_table, fill_table


class GameAutomationTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Game automation is preview-only. Rule edits save app JSON; auto-apply is forced false in Phase 3."))

        layout.addWidget(QLabel("Manifest game/automation controls"))
        self.controls_table = QTableWidget()
        layout.addWidget(self.controls_table, 1)
        fill_controls_table(self.controls_table, self.surface.by_tab("Game Automation"))

        layout.addWidget(QLabel("Editable process rules"))
        self.rules_table = QTableWidget()
        layout.addWidget(self.rules_table, 1)
        self.load_rules()

        buttons = QHBoxLayout()
        for text, callback in [
            ("Save Game Rules JSON", self.save_rules),
            ("Refresh Running Processes", self.refresh_matches),
            ("Preview Rule Match", self.preview_rule),
            ("Export Process Snapshot", self.export_snapshot),
        ]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.matches_table = QTableWidget()
        layout.addWidget(QLabel("Live process matching preview"))
        layout.addWidget(self.matches_table, 1)
        self.warning = QTextEdit()
        self.warning.setReadOnly(True)
        self.warning.setPlainText(
            "Special handling: java/javaw are broad and require command-line filtering. "
            "Steam webhelper does not count as a game. BF6 process names remain seed guesses until confirmed from a real session."
        )
        layout.addWidget(self.warning)
        self.refresh_matches()

    def load_rules(self) -> None:
        headers = ["Enabled", "Target ID", "Friendly name", "Processes", "Command-line contains", "Launcher association", "CPU preset later", "GPU slot later", "Restore on exit", "Auto-apply later"]
        rules = self.surface.game_rules.get("rules", [])
        self.rules_table.setColumnCount(len(headers))
        self.rules_table.setHorizontalHeaderLabels(headers)
        self.rules_table.setRowCount(len(rules))
        for row, rule in enumerate(rules):
            values = [
                rule.get("enabled"),
                rule.get("target_id"),
                rule.get("friendly_name"),
                ", ".join(rule.get("process_names", [])),
                ", ".join(rule.get("command_line_contains", [])),
                rule.get("launcher_association"),
                rule.get("cpu_preset_to_use_later"),
                rule.get("gpu_profile_slot_to_use_later"),
                rule.get("restore_on_exit_later"),
                False,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                if col in {1, 9}:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.rules_table.setItem(row, col, item)
        self.rules_table.resizeColumnsToContents()

    def save_rules(self) -> None:
        rules = self.surface.game_rules.get("rules", [])
        for row, rule in enumerate(rules):
            rule["enabled"] = self._bool(row, 0)
            rule["friendly_name"] = self._text(row, 2)
            rule["process_names"] = [part.strip() for part in self._text(row, 3).split(",") if part.strip()]
            rule["command_line_contains"] = [part.strip() for part in self._text(row, 4).split(",") if part.strip()]
            rule["launcher_association"] = self._text(row, 5) or None
            rule["cpu_preset_to_use_later"] = self._text(row, 6) or None
            gpu_slot = self._text(row, 7)
            rule["gpu_profile_slot_to_use_later"] = int(gpu_slot) if gpu_slot.isdigit() else None
            rule["restore_on_exit_later"] = self._bool(row, 8)
            rule["auto_apply_enabled_later"] = False
        path = self.surface.save_game_rules()
        QMessageBox.information(self, "Game rules saved", f"Saved app-side rules only:\n{path}")

    def refresh_matches(self) -> None:
        self.rows = self.window.processes.match_targets()
        fill_table(
            self.matches_table,
            ["Target ID", "Friendly", "Category", "Running now", "Matched processes", "False-positive risk"],
            [
                [
                    row.get("id"),
                    row.get("friendly"),
                    row.get("category"),
                    row.get("running_now"),
                    ", ".join([str(proc.get("ProcessName")) for proc in row.get("matched_processes", [])]),
                    self._false_positive_note(row),
                ]
                for row in self.rows
            ],
        )

    def preview_rule(self) -> None:
        row = self.matches_table.currentRow()
        if row < 0 or row >= len(getattr(self, "rows", [])):
            QMessageBox.information(self, "No rule selected", "Select a live match row first.")
            return
        QMessageBox.information(self, "Preview only", str(self.rows[row]) + "\n\nNo preset is applied in Phase 3.")

    def export_snapshot(self) -> None:
        target = self.window.paths.raw_outputs_dir / f"process_snapshot_{time.strftime('%Y%m%d-%H%M%S')}.json"
        save_json_inside_phase3(target, {"targets": getattr(self, "rows", [])}, self.window.paths)
        QMessageBox.information(self, "Exported", str(target))

    def _text(self, row: int, col: int) -> str:
        item = self.rules_table.item(row, col)
        return item.text().strip() if item else ""

    def _bool(self, row: int, col: int) -> bool:
        return self._text(row, col).lower() in {"true", "1", "yes", "enabled"}

    def _false_positive_note(self, row: dict) -> str:
        names = [name.lower() for name in row.get("process_names", [])]
        if "java" in names or "javaw" in names:
            return "Broad Java process; command-line filter required"
        if row.get("id") == "steam":
            return "Launcher/webhelper only, not a game by itself"
        if row.get("id") == "battlefield_6":
            return "Seed guess until real BF6 session confirms process"
        return "normal"
