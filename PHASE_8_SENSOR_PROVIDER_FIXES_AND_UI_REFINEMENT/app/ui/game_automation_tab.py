from __future__ import annotations

import time

from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTextEdit, QWidget

from app.core.config_loader import save_json_inside_phase3
from app.ui.common import add_form_row, fill_table, make_card, make_metric, make_page_header, make_scroll_page


class GameAutomationTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        self.rule_widgets: list[dict] = []
        layout, _body = make_scroll_page(self)
        layout.addWidget(
            make_page_header(
                "Game Automation",
                "Edit process detection rules and future preset targets. Detection is live; automation apply remains disabled.",
                [("Automation disabled", "safe"), ("Detection read-only", "neutral")],
            )
        )

        metrics = QHBoxLayout()
        metric_panel = QWidget()
        metric_panel.setLayout(metrics)
        metrics.addWidget(make_metric("Rules", str(len(self.surface.game_rules.get("rules", [])))))
        metrics.addWidget(make_metric("Automation apply", "False", "safe"))
        metrics.addStretch(1)
        layout.addWidget(metric_panel)

        editor_card, editor_layout = make_card("Editable process rules", "Rules save to presets/game_rules.json. Matching a process never applies a preset in this phase.")
        self.rule_editor = QWidget()
        self.rule_editor.setObjectName("game_rule_editor")
        self.rule_layout = QHBoxLayout(self.rule_editor)
        self.rule_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self.rule_editor)
        layout.addWidget(editor_card)
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

        matches_card, matches_layout = make_card("Live process matching", "Read-only running process summary.")
        self.matches_table = QTableWidget()
        self.matches_table.setObjectName("process_command_line_table")
        matches_layout.addWidget(self.matches_table)
        layout.addWidget(matches_card)

        warning_card, warning_layout = make_card("Detection notes")
        self.warning = QTextEdit()
        self.warning.setReadOnly(True)
        self.warning.setPlainText(
            "java/javaw are broad and require command-line filtering. Steam webhelper does not count as a game. BF6 process names remain seed guesses until confirmed from a real session."
        )
        warning_layout.addWidget(self.warning)
        layout.addWidget(warning_card)
        layout.addStretch(1)
        self.refresh_matches()

    def load_rules(self) -> None:
        while self.rule_layout.count():
            item = self.rule_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.rule_widgets = []

        from PySide6.QtWidgets import QVBoxLayout

        columns = [QWidget(), QWidget()]
        bodies = []
        for column in columns:
            body = QVBoxLayout()
            body.setContentsMargins(0, 0, 0, 0)
            body.setSpacing(12)
            column.setLayout(body)
            bodies.append(body)

        cpu_names = [preset.get("name", "") for preset in self.surface.cpu_presets.get("presets", []) if preset.get("name")]
        gpu_slots = [""] + [str(slot.get("slot")) for slot in self.surface.gpu_profiles.get("slots", [])]
        for index, rule in enumerate(self.surface.game_rules.get("rules", [])):
            card, card_layout = make_card(rule.get("friendly_name") or rule.get("target_id"), f"Target ID: {rule.get('target_id')}")
            enabled = QCheckBox("Detection enabled")
            enabled.setChecked(bool(rule.get("enabled")))
            friendly = QLineEdit(str(rule.get("friendly_name") or ""))
            processes = QLineEdit(", ".join(rule.get("process_names", [])))
            command_line = QLineEdit(", ".join(rule.get("command_line_contains", [])))
            launcher = QLineEdit(str(rule.get("launcher_association") or ""))
            cpu = QComboBox()
            cpu.addItems([""] + cpu_names)
            cpu.setCurrentText(str(rule.get("cpu_preset_to_use_later") or ""))
            gpu = QComboBox()
            gpu.addItems(gpu_slots)
            current_gpu = "" if rule.get("gpu_profile_slot_to_use_later") is None else str(rule.get("gpu_profile_slot_to_use_later"))
            gpu.setCurrentText(current_gpu)
            restore = QCheckBox("Restore on exit later")
            restore.setChecked(bool(rule.get("restore_on_exit_later")))
            auto_apply = QCheckBox("Auto-apply later")
            auto_apply.setChecked(False)
            auto_apply.setEnabled(False)
            card_layout.addWidget(enabled)
            add_form_row(card_layout, "Friendly name", friendly)
            add_form_row(card_layout, "Process names", processes, "Comma-separated executable names.")
            add_form_row(card_layout, "Command-line contains", command_line, "Optional comma-separated filters.")
            add_form_row(card_layout, "Launcher association", launcher)
            add_form_row(card_layout, "Future CPU preset", cpu)
            add_form_row(card_layout, "Future GPU slot", gpu)
            card_layout.addWidget(restore)
            card_layout.addWidget(auto_apply)
            bodies[index % 2].addWidget(card)
            self.rule_widgets.append({"rule": rule, "enabled": enabled, "friendly": friendly, "processes": processes, "command": command_line, "launcher": launcher, "cpu": cpu, "gpu": gpu, "restore": restore})

        for body in bodies:
            body.addStretch(1)
        self.rule_layout.addWidget(columns[0], 1)
        self.rule_layout.addWidget(columns[1], 1)

    def save_rules(self) -> None:
        for row in self.rule_widgets:
            rule = row["rule"]
            rule["enabled"] = row["enabled"].isChecked()
            rule["friendly_name"] = row["friendly"].text().strip()
            rule["process_names"] = [part.strip() for part in row["processes"].text().split(",") if part.strip()]
            rule["command_line_contains"] = [part.strip() for part in row["command"].text().split(",") if part.strip()]
            rule["launcher_association"] = row["launcher"].text().strip() or None
            rule["cpu_preset_to_use_later"] = row["cpu"].currentText() or None
            gpu_slot = row["gpu"].currentText()
            rule["gpu_profile_slot_to_use_later"] = int(gpu_slot) if gpu_slot.isdigit() else None
            rule["restore_on_exit_later"] = row["restore"].isChecked()
            rule["auto_apply_enabled_later"] = False
        path = self.surface.save_game_rules()
        QMessageBox.information(self, "Game rules saved", f"Saved app-side rules only:\n{path}")

    def refresh_matches(self) -> None:
        self.rows = self.window.processes.match_targets()
        fill_table(
            self.matches_table,
            ["Target ID", "Friendly", "Category", "Running now", "Matched processes", "Command line matched", "Command line unavailable", "False-positive warning", "Automation apply"],
            [
                [
                    row.get("id"),
                    row.get("friendly"),
                    row.get("category"),
                    row.get("running_now"),
                    ", ".join([f"{proc.get('ProcessName')}[{proc.get('ProcessId')}]" for proc in row.get("matched_processes", [])]),
                    row.get("command_line_matched"),
                    row.get("command_line_unavailable"),
                    row.get("false_positive_warning") or self._false_positive_note(row),
                    False,
                ]
                for row in self.rows
            ],
        )

    def preview_rule(self) -> None:
        row = self.matches_table.currentRow()
        if row < 0 or row >= len(getattr(self, "rows", [])):
            QMessageBox.information(self, "No rule selected", "Select a live match row first.")
            return
        QMessageBox.information(self, "Preview only", str(self.rows[row]) + "\n\nNo preset is applied.")

    def export_snapshot(self) -> None:
        target = self.window.paths.raw_outputs_dir / f"process_snapshot_{time.strftime('%Y%m%d-%H%M%S')}.json"
        save_json_inside_phase3(target, {"targets": getattr(self, "rows", [])}, self.window.paths)
        QMessageBox.information(self, "Exported", str(target))

    def _false_positive_note(self, row: dict) -> str:
        names = [name.lower() for name in row.get("process_names", [])]
        if "java" in names or "javaw" in names:
            return "Broad Java process; command-line filter required"
        if row.get("id") == "steam":
            return "Launcher/webhelper only, not a game by itself"
        if row.get("id") == "battlefield_6":
            return "Seed guess until real BF6 session confirms process"
        return "normal"
