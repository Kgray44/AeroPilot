from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QTextEdit, QVBoxLayout, QWidget

from app.core.risk_model import RISK_LABELS
from app.ui.common import fill_table, make_badge


class SettingsSafetyTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        layout = QVBoxLayout(self)
        layout.addWidget(make_badge("Safety mode: READ-ONLY / DRY-RUN", "safe"))
        layout.addWidget(QLabel("All apply actions are disabled in Phase 3. Editable controls write only Phase 3 JSON."))
        layout.addWidget(QLabel("Risk labels: " + ", ".join(RISK_LABELS)))

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
            "- Disable all apply actions: app config true in Phase 3",
            "- Disable automation: app config true in Phase 3",
            "- Disable startup behavior: app config true in Phase 3",
            "- Restore last known safe state: future only",
            "- Panic restore: future only",
        ]
        self.missing.setPlainText("\n".join(lines))
