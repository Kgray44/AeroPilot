from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from app.ui.common import fill_controls_table


class AutoTuningTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Auto tuning is definition-only in Phase 3. No benchmark, capture, scoring, or apply action is run."))

        layout.addWidget(QLabel("Related manifest controls"))
        self.controls_table = QTableWidget()
        controls = [c for c in self.surface.controls if c.get("ui_tab") == "Auto Tuning" or c.get("control_id", "").startswith("network.")]
        fill_controls_table(self.controls_table, controls)
        layout.addWidget(self.controls_table, 1)

        layout.addWidget(QLabel("Editable experiment plans saved inside presets/combined_presets.json"))
        self.plan_table = QTableWidget()
        layout.addWidget(self.plan_table, 1)
        self.load_plans()

        buttons = QHBoxLayout()
        save = QPushButton("Save Experiment Plans JSON")
        save.clicked.connect(self.save_plans)
        buttons.addWidget(save)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        scoring = QTextEdit()
        scoring.setReadOnly(True)
        scoring.setPlainText(
            "\n".join(
                [
                    "Future scoring model preview:",
                    "- Average FPS",
                    "- 1 percent low",
                    "- Frame-time stability",
                    "- GPU utilization",
                    "- CPU saturation",
                    "- GPU power",
                    "- GPU temperature",
                    "- Ping average",
                    "- Ping spikes",
                    "- Crash/driver reset flag",
                    "",
                    "BF6 planned scoring:",
                    "- Penalize CPU pegged near 100%",
                    "- Penalize ping spikes",
                    "- Penalize low GPU utilization when FPS is poor",
                    "- Reward stable frame-time and stable ping",
                ]
            )
        )
        layout.addWidget(scoring)

    def load_plans(self) -> None:
        plans = self.surface.combined_presets.get("experiment_plans", [])
        headers = ["Experiment", "Target", "CPU candidates", "GPU candidates", "Metrics", "Duration", "Success criteria", "Failure criteria", "Restore behavior"]
        self.plan_table.setColumnCount(len(headers))
        self.plan_table.setHorizontalHeaderLabels(headers)
        self.plan_table.setRowCount(len(plans))
        for row, plan in enumerate(plans):
            values = [
                plan.get("experiment_name"),
                plan.get("target_game_process"),
                ", ".join(plan.get("cpu_preset_candidates", [])),
                ", ".join(str(v) for v in plan.get("gpu_profile_candidates", [])),
                ", ".join(plan.get("metrics_to_capture", [])),
                plan.get("duration_seconds"),
                plan.get("success_criteria"),
                plan.get("failure_criteria"),
                plan.get("restore_behavior"),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                if col == 8:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.plan_table.setItem(row, col, item)
        self.plan_table.resizeColumnsToContents()

    def save_plans(self) -> None:
        plans = self.surface.combined_presets.get("experiment_plans", [])
        for row, plan in enumerate(plans):
            plan["experiment_name"] = self._text(row, 0)
            plan["target_game_process"] = self._text(row, 1)
            plan["cpu_preset_candidates"] = [part.strip() for part in self._text(row, 2).split(",") if part.strip()]
            plan["gpu_profile_candidates"] = [int(part.strip()) for part in self._text(row, 3).split(",") if part.strip().isdigit()]
            plan["metrics_to_capture"] = [part.strip() for part in self._text(row, 4).split(",") if part.strip()]
            duration = self._text(row, 5)
            plan["duration_seconds"] = int(duration) if duration.isdigit() else 0
            plan["success_criteria"] = self._text(row, 6)
            plan["failure_criteria"] = self._text(row, 7)
            plan["phase3_status"] = "definition_only"
        path = self.surface.save_combined_presets()
        QMessageBox.information(self, "Experiment plans saved", f"Saved definitions only:\n{path}")

    def _text(self, row: int, col: int) -> str:
        item = self.plan_table.item(row, col)
        return item.text().strip() if item else ""
