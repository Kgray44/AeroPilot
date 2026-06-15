from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTextEdit, QWidget

from app.ui.common import add_form_row, make_card, make_metric, make_page_header, make_scroll_page


METRIC_OPTIONS = [
    "average_fps",
    "one_percent_low",
    "frametime_ms",
    "gpu_utilization",
    "cpu_saturation",
    "gpu_power",
    "gpu_temperature",
    "ping_average",
    "ping_spikes",
]
RESTORE_OPTIONS = ["restore_previous_state", "manual_restore_only", "do_not_restore"]


class AutoTuningTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        self.plan_widgets: list[dict] = []
        layout, _body = make_scroll_page(self)
        layout.addWidget(
            make_page_header(
                "Auto Tuning",
                "Design future tuning experiments without running benchmarks, captures, scoring, or apply actions.",
                [("Definition only", "safe"), ("No tuning run", "neutral")],
            )
        )

        metrics = QHBoxLayout()
        metric_panel = QWidget()
        metric_panel.setLayout(metrics)
        metrics.addWidget(make_metric("Experiment plans", str(len(self.surface.combined_presets.get("experiment_plans", [])))))
        metrics.addWidget(make_metric("Apply automation", "False", "safe"))
        metrics.addStretch(1)
        layout.addWidget(metric_panel)

        editor_card, editor_layout = make_card("Editable experiment plans", "Saved inside presets/combined_presets.json. These are future run definitions only.")
        self.plan_editor = QWidget()
        self.plan_editor.setObjectName("experiment_plan_editor")
        self.plan_layout = QHBoxLayout(self.plan_editor)
        self.plan_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self.plan_editor)
        layout.addWidget(editor_card)
        self.load_plans()

        button_row = QHBoxLayout()
        save = QPushButton("Save Experiment Plans JSON")
        save.clicked.connect(self.save_plans)
        button_row.addWidget(save)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        scoring_card, scoring_layout = make_card("Scoring preview", "A future scoring model can compare presets after guarded telemetry capture exists.")
        scoring = QTextEdit()
        scoring.setReadOnly(True)
        scoring.setPlainText(
            "\n".join(
                [
                    "Future scoring model:",
                    "- Average FPS",
                    "- 1 percent low",
                    "- Frame-time stability",
                    "- GPU utilization and temperature",
                    "- CPU saturation",
                    "- Ping average and spikes",
                    "- Crash/driver reset flag",
                    "",
                    "No tuning run is started from this tab.",
                ]
            )
        )
        scoring_layout.addWidget(scoring)
        layout.addWidget(scoring_card)
        layout.addStretch(1)

    def load_plans(self) -> None:
        while self.plan_layout.count():
            item = self.plan_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.plan_widgets = []
        from PySide6.QtWidgets import QVBoxLayout

        columns = [QWidget(), QWidget()]
        bodies = []
        for column in columns:
            body = QVBoxLayout()
            body.setContentsMargins(0, 0, 0, 0)
            body.setSpacing(12)
            column.setLayout(body)
            bodies.append(body)

        target_ids = [rule.get("target_id", "") for rule in self.surface.game_rules.get("rules", []) if rule.get("target_id")]
        cpu_names = [preset.get("name", "") for preset in self.surface.cpu_presets.get("presets", []) if preset.get("name")]
        gpu_slots = [str(slot.get("slot")) for slot in self.surface.gpu_profiles.get("slots", [])]
        for index, plan in enumerate(self.surface.combined_presets.get("experiment_plans", [])):
            card, card_layout = make_card(plan.get("experiment_name") or "Experiment", "Definition only.")
            name = QLineEdit(str(plan.get("experiment_name") or ""))
            target = QComboBox()
            target.addItems([""] + target_ids)
            target.setCurrentText(str(plan.get("target_game_process") or ""))
            cpu = QLineEdit(", ".join(plan.get("cpu_preset_candidates", [])))
            cpu.setPlaceholderText(", ".join(cpu_names[:3]))
            gpu = QLineEdit(", ".join(str(v) for v in plan.get("gpu_profile_candidates", [])))
            gpu.setPlaceholderText(", ".join(gpu_slots))
            metric_text = QLineEdit(", ".join(plan.get("metrics_to_capture", [])))
            metric_text.setPlaceholderText(", ".join(METRIC_OPTIONS[:4]))
            duration = QSpinBox()
            duration.setRange(0, 7200)
            duration.setValue(int(plan.get("duration_seconds") or 0))
            success = QLineEdit(str(plan.get("success_criteria") or ""))
            failure = QLineEdit(str(plan.get("failure_criteria") or ""))
            restore = QComboBox()
            restore.addItems(RESTORE_OPTIONS)
            restore.setCurrentText(str(plan.get("restore_behavior") or RESTORE_OPTIONS[0]))
            add_form_row(card_layout, "Experiment name", name)
            add_form_row(card_layout, "Target process", target)
            add_form_row(card_layout, "CPU candidates", cpu, "Comma-separated preset names.")
            add_form_row(card_layout, "GPU slots", gpu, "Comma-separated slot numbers.")
            add_form_row(card_layout, "Metrics", metric_text, "Comma-separated metrics.")
            add_form_row(card_layout, "Duration seconds", duration)
            add_form_row(card_layout, "Success criteria", success)
            add_form_row(card_layout, "Failure criteria", failure)
            add_form_row(card_layout, "Restore behavior", restore)
            bodies[index % 2].addWidget(card)
            self.plan_widgets.append({"plan": plan, "name": name, "target": target, "cpu": cpu, "gpu": gpu, "metrics": metric_text, "duration": duration, "success": success, "failure": failure, "restore": restore})

        for body in bodies:
            body.addStretch(1)
        self.plan_layout.addWidget(columns[0], 1)
        self.plan_layout.addWidget(columns[1], 1)

    def save_plans(self) -> None:
        for row in self.plan_widgets:
            plan = row["plan"]
            plan["experiment_name"] = row["name"].text().strip()
            plan["target_game_process"] = row["target"].currentText() or None
            plan["cpu_preset_candidates"] = [part.strip() for part in row["cpu"].text().split(",") if part.strip()]
            plan["gpu_profile_candidates"] = [int(part.strip()) for part in row["gpu"].text().split(",") if part.strip().isdigit()]
            plan["metrics_to_capture"] = [part.strip() for part in row["metrics"].text().split(",") if part.strip()]
            plan["duration_seconds"] = int(row["duration"].value())
            plan["success_criteria"] = row["success"].text().strip()
            plan["failure_criteria"] = row["failure"].text().strip()
            plan["restore_behavior"] = row["restore"].currentText()
            plan["phase3_status"] = "definition_only"
            plan["phase4_status"] = "definition_only"
        path = self.surface.save_combined_presets()
        QMessageBox.information(self, "Experiment plans saved", f"Saved definitions only:\n{path}")
