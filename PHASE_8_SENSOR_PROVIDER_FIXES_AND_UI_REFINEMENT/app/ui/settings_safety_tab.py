from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTextEdit, QVBoxLayout, QWidget

from app.core.config_loader import load_json
from app.core.risk_model import RISK_LABELS
from app.ui.common import add_form_row, fill_table, make_badge, make_card


class SettingsSafetyTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        layout = QVBoxLayout(self)
        layout.addWidget(make_badge("Safety mode: READ-ONLY / DRY-RUN", "safe"))
        layout.addWidget(QLabel("Phase 8 is telemetry, diagnostics, and UI only. Active plan writes, MSI profile launches, NVIDIA writes, fan controls, embedded-controller paths, services, startup entries, scheduled tasks, registry writes, and automation apply remain disabled."))
        layout.addWidget(QLabel("Risk labels: " + ", ".join(RISK_LABELS)))

        gates = load_json(self.window.paths.config_dir / "apply_gate_config.json", {})
        backup = load_json(self.window.paths.phase4_root / "backups" / "backup_manifest_latest.json", {})
        restore = load_json(self.window.paths.phase4_root / "restore" / "restore_manifest_latest.json", {})
        sandbox = load_json(self.window.paths.phase4_root / "sandbox" / "sandbox_powercfg_test_result.json", {})
        self.phase4_table = QTableWidget()
        layout.addWidget(QLabel("Phase 5 backup / restore / apply gates"))
        layout.addWidget(self.phase4_table)
        fill_table(
            self.phase4_table,
            ["Item", "Status"],
            [
                ["Backup manifest", "present" if backup else "missing"],
                ["Restore manifest", "present" if restore else "missing"],
                ["Sandbox test passed", sandbox.get("passed", "not run")],
                ["cpu_guarded_apply_enabled", gates.get("cpu_guarded_apply_enabled", False)],
                ["cpu_restore_available", gates.get("cpu_restore_available", False)],
                ["active_plan_write_enabled", gates.get("active_plan_write_enabled", False)],
                ["msi_profile_apply_enabled", gates.get("msi_profile_apply_enabled", False)],
                ["fan_write_enabled", gates.get("fan_write_enabled", False)],
                ["ec_write_enabled", gates.get("ec_write_enabled", False)],
                ["automation_apply_enabled", gates.get("automation_apply_enabled", False)],
            ],
        )

        sensor_card, sensor_layout = make_card("Sensor configuration and safety", "Sensor favorites and polling preferences are app-side JSON only.")
        self.sensor_config_table = QTableWidget()
        sensor_layout.addWidget(self.sensor_config_table)
        layout.addWidget(sensor_card)
        polling = self.surface.app_config.get("polling", {})
        sensor_model = self.window.latest_sensor_model
        headline = sensor_model.get("headline", {})
        cpu_provider = sensor_model.get("diagnostics", {}).get("cpu_provider", {})
        fill_table(
            self.sensor_config_table,
            ["Item", "Status"],
            [
                ["polling enabled", polling.get("enabled", False)],
                ["polling interval", polling.get("interval_seconds", "default")],
                ["telemetry logging enabled", polling.get("log_telemetry_snapshots", False)],
                ["sensor favorites config present", (self.window.paths.config_dir / "sensor_favorites.json").exists()],
                ["favorite sensor count", len(self.window.sensor_favorites.get("favorites", []))],
                ["last sensor normalization status", "ok" if sensor_model.get("ok") else "waiting or unavailable"],
                ["last sensor count", len(sensor_model.get("raw_sensors", []))],
                ["CPU provider health", headline.get("cpu_provider_health", "unknown")],
                ["CPU load valid", headline.get("cpu_load_percent") is not None],
                ["CPU temp valid", headline.get("cpu_temp_c") is not None],
                ["CPU power valid", headline.get("cpu_power_w") is not None],
                ["CPU clock valid", headline.get("cpu_clock_mhz") is not None],
                ["CPU voltage valid", headline.get("cpu_voltage_v") is not None],
                ["CPU stale-zero count", cpu_provider.get("stale_zero_count", 0)],
                ["CPU invalid count", cpu_provider.get("invalid_count", 0)],
                ["apply gates remain blocked", not gates.get("active_plan_write_enabled", False) and not gates.get("msi_profile_apply_enabled", False)],
            ],
        )

        plan_card, plan_layout = make_card("Power plan management", "Read all Windows power plans. Create/set actions are preview-only and locked in Phase 5.")
        plan_card.setObjectName("power_plan_management_panel")
        plan_controls = QHBoxLayout()
        self.power_plan_box = QComboBox()
        self.new_plan_name = QLineEdit("AeroTune cloned plan preview")
        refresh_plans = QPushButton("Refresh Power Plans")
        refresh_plans.clicked.connect(self.refresh_power_plans)
        self.create_preview = QPushButton("Preview Create/Clone Plan")
        self.create_preview.setObjectName("power_plan_create_preview_button")
        self.create_preview.clicked.connect(self.preview_create_plan)
        self.set_preview = QPushButton("Preview Set Active Plan")
        self.set_preview.setObjectName("power_plan_set_preview_button")
        self.set_preview.clicked.connect(self.preview_set_plan)
        self.create_apply = QPushButton("Create Plan Locked")
        self.create_apply.setObjectName("power_plan_create_apply_button")
        self.create_apply.setEnabled(False)
        self.set_apply = QPushButton("Set Active Locked")
        self.set_apply.setObjectName("power_plan_set_apply_button")
        self.set_apply.setEnabled(False)
        plan_controls.addWidget(refresh_plans)
        plan_controls.addWidget(self.create_preview)
        plan_controls.addWidget(self.set_preview)
        plan_controls.addWidget(self.create_apply)
        plan_controls.addWidget(self.set_apply)
        plan_controls.addStretch(1)
        add_form_row(plan_layout, "Existing plan", self.power_plan_box)
        add_form_row(plan_layout, "New clone name", self.new_plan_name)
        plan_layout.addLayout(plan_controls)
        self.power_plan_preview = QTextEdit()
        self.power_plan_preview.setReadOnly(True)
        self.power_plan_preview.setMinimumHeight(90)
        plan_layout.addWidget(self.power_plan_preview)
        self.power_plan_table = QTableWidget()
        self.power_plan_table.setObjectName("power_plan_list_table")
        plan_layout.addWidget(self.power_plan_table)
        layout.addWidget(plan_card)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search coverage")
        self.search.textChanged.connect(self.refresh)
        self.risk_filter = QComboBox()
        self.risk_filter.addItem("All")
        self.risk_filter.addItems(RISK_LABELS)
        self.risk_filter.currentTextChanged.connect(self.refresh)
        self.tab_filter = QComboBox()
        self.tab_filter.addItem("All")
        self.tab_filter.addItems(sorted({row.get("ui_tab") for row in self.surface.controls}))
        self.tab_filter.currentTextChanged.connect(self.refresh)
        filters.addWidget(self.search, 2)
        filters.addWidget(QLabel("Risk"))
        filters.addWidget(self.risk_filter)
        filters.addWidget(QLabel("Tab"))
        filters.addWidget(self.tab_filter)
        layout.addLayout(filters)

        layout.addWidget(QLabel("Risk catalog coverage"))
        self.risk_table = QTableWidget()
        layout.addWidget(self.risk_table, 1)

        layout.addWidget(QLabel("Control coverage matrix"))
        self.coverage_table = QTableWidget()
        layout.addWidget(self.coverage_table, 2)

        self.missing = QTextEdit()
        self.missing.setReadOnly(True)
        layout.addWidget(QLabel("Missing coverage warnings and future safety"))
        layout.addWidget(self.missing)
        self.refresh()
        self.refresh_power_plans()

    def refresh_power_plans(self) -> None:
        self.power_plans = self.window.power_plans.list_schemes()
        self.power_plan_box.clear()
        for plan in self.power_plans:
            suffix = " (active)" if plan.get("active") else ""
            self.power_plan_box.addItem(f"{plan.get('name')} - {plan.get('guid')}{suffix}", plan.get("guid"))
        fill_table(
            self.power_plan_table,
            ["Name", "GUID", "Active", "Preview-only status"],
            [[plan.get("name"), plan.get("guid"), plan.get("active"), "create/set locked in Phase 5"] for plan in self.power_plans],
        )

    def preview_create_plan(self) -> None:
        source_guid = self.power_plan_box.currentData() or "<source_scheme_guid>"
        preview = self.window.power_plans.create_clone_preview(source_guid, self.new_plan_name.text())
        self.power_plan_preview.setPlainText("\n".join(["PREVIEW ONLY"] + preview.get("commands", []) + [preview.get("explanation", "")]))

    def preview_set_plan(self) -> None:
        target_guid = self.power_plan_box.currentData() or "<target_scheme_guid>"
        preview = self.window.power_plans.set_active_preview(target_guid)
        self.power_plan_preview.setPlainText("\n".join(["PREVIEW ONLY"] + preview.get("commands", []) + [preview.get("explanation", "")]))

    def refresh(self) -> None:
        query = self.search.text().lower()
        risk = self.risk_filter.currentText()
        tab = self.tab_filter.currentText()

        controls = self.surface.search(query, risk=risk, tab=tab)
        manifest_names = {c.get("source", {}).get("phase1_risk_name") or c.get("friendly_name") for c in self.surface.controls}
        risk_rows = []
        for item in self.window.risk_model.items:
            represented = item.get("setting_control_name") in manifest_names
            appears = any(c.get("source", {}).get("phase1_risk_name") == item.get("setting_control_name") for c in self.surface.controls)
            risk_rows.append(
                [
                    item.get("setting_control_name"),
                    item.get("category"),
                    item.get("risk_level"),
                    represented,
                    appears,
                    item.get("suggested_warning_label"),
                ]
            )
        fill_table(self.risk_table, ["Risk item", "Category", "Risk", "In manifest", "In GUI", "Warning"], risk_rows)

        coverage_rows = []
        wanted_ids = {c.get("control_id") for c in controls}
        for row in self.surface.coverage_rows:
            if row.get("control_id") not in wanted_ids:
                continue
            coverage_rows.append(
                [
                    row.get("control_id"),
                    row.get("friendly_name"),
                    row.get("category"),
                    row.get("risk"),
                    row.get("ui_tab"),
                    row.get("ui_section"),
                    row.get("current_readable"),
                    row.get("editable"),
                    row.get("dry_run_preview"),
                    row.get("backup_strategy"),
                    row.get("restore_strategy"),
                    row.get("validation"),
                ]
            )
        fill_table(
            self.coverage_table,
            ["control_id", "friendly name", "category", "risk", "ui_tab", "ui_section", "readable", "editable", "dry-run", "backup", "restore", "validation"],
            coverage_rows,
        )

        missing = [row for row in self.surface.coverage_rows if row.get("validation") != "pass"]
        lines = [
            f"Missing coverage rows: {len(missing)}",
            "",
            "Future kill-switches / safety controls:",
            "- Disable all apply actions: enforced false in Phase 4 gates",
            "- Disable automation: enforced false in Phase 4 gates",
            "- Disable startup behavior: still blocked",
            "- Restore last known safe state: future only",
            "- Panic restore: future only",
        ]
        self.missing.setPlainText("\n".join(lines))
