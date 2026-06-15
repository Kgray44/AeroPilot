from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QVBoxLayout, QWidget

from app.core.dryrun import powercfg_setting_preview
from app.ui.common import fill_table


class CpuTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("CPU settings from Phase 1. Apply actions are disabled; previews are dry-run only."))

        self.table = QTableWidget()
        layout.addWidget(self.table, 1)
        self.load_table()

        layout.addWidget(QLabel("Placeholder preset previews"))
        self.preset_table = QTableWidget()
        layout.addWidget(self.preset_table)
        fill_table(
            self.preset_table,
            ["Preset", "Status", "Risk", "Apply"],
            [
                ["Stock / Restore", "Preview only", "Safe", "Disabled"],
                ["Quiet School Mode", "Preview only", "Medium", "Dry-run dialog only"],
                ["Gaming Balanced", "Preview only", "Medium", "Dry-run dialog only"],
                ["BF6 Emergency", "Preview only", "High", "Dry-run dialog only"],
                ["Benchmark Mode", "Preview only", "High", "Dry-run dialog only"],
            ],
        )

        buttons = QHBoxLayout()
        refresh = QPushButton("Refresh Selected Setting Read-only")
        refresh.clicked.connect(self.refresh_selected)
        preview = QPushButton("Preview CPU Dry-run Command")
        preview.clicked.connect(self.preview_selected)
        buttons.addWidget(refresh)
        buttons.addWidget(preview)
        buttons.addStretch(1)
        layout.addLayout(buttons)

    def load_table(self) -> None:
        rows = []
        for setting in self.window.phase1.cpu_settings():
            possible = ", ".join([str(v.get("name")) for v in setting.get("possible_values", [])]) or ""
            rows.append(
                [
                    setting.get("friendly_name"),
                    setting.get("alias"),
                    setting.get("setting_guid"),
                    setting.get("current_ac_value"),
                    setting.get("current_dc_value"),
                    possible,
                    setting.get("risk_level"),
                    "readable" if setting.get("powercfg_can_read") else "not readable",
                    "disabled in Phase 2",
                    setting.get("suggested_future_tooltip_warning"),
                ]
            )
        fill_table(
            self.table,
            [
                "Friendly name",
                "Alias",
                "Setting GUID",
                "Current AC",
                "Current DC",
                "Possible values",
                "Risk",
                "Reachability",
                "Future write status",
                "Warning",
            ],
            rows,
        )

    def selected_setting(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        settings = self.window.phase1.cpu_settings()
        return settings[row] if row < len(settings) else None

    def refresh_selected(self) -> None:
        setting = self.selected_setting()
        if not setting:
            QMessageBox.information(self, "No setting selected", "Select a CPU setting first.")
            return
        result = self.window.power.refresh_setting(setting.get("subgroup_guid"), setting.get("setting_guid"))
        QMessageBox.information(self, "Read-only powercfg result", result.get("raw")[:3000] or str(result))

    def preview_selected(self) -> None:
        setting = self.selected_setting()
        if not setting:
            QMessageBox.information(self, "No setting selected", "Select a CPU setting first.")
            return
        preview = powercfg_setting_preview(
            self.window.phase1.powercfg().get("active_scheme_guid", "SCHEME_CURRENT"),
            setting.get("subgroup_guid"),
            setting.get("setting_guid"),
            setting.get("current_ac_value", 0),
            "AC",
            setting.get("risk_level", "Unknown"),
        )
        QMessageBox.warning(
            self,
            "Dry-run only",
            preview.command_line()
            + "\n\n"
            + preview.explanation
            + "\n\n"
            + preview.phase2_reason_not_executed,
        )
