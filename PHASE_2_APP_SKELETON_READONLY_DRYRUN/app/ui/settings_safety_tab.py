from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QVBoxLayout, QWidget

from app.core.risk_model import RISK_LABELS
from app.ui.common import fill_table, make_badge


class SettingsSafetyTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.addWidget(make_badge("Safety mode: READ-ONLY / DRY-RUN", "safe"))
        layout.addWidget(QLabel("All apply actions are disabled in Phase 2. High-risk actions require backup, restore, confirmation, and a later approved phase."))
        layout.addWidget(QLabel("Risk labels: " + ", ".join(RISK_LABELS)))

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search risk catalog")
        self.search.textChanged.connect(self.refresh)
        self.risk_filter = QComboBox()
        self.risk_filter.addItem("All")
        self.risk_filter.addItems(RISK_LABELS)
        self.risk_filter.currentTextChanged.connect(self.refresh)
        filters.addWidget(self.search)
        filters.addWidget(self.risk_filter)
        layout.addLayout(filters)

        self.table = QTableWidget()
        layout.addWidget(self.table, 1)
        self.refresh()

    def refresh(self) -> None:
        query = self.search.text().lower()
        risk = self.risk_filter.currentText()
        rows = []
        for item in self.window.risk_model.items:
            haystack = " ".join(str(v) for v in item.values()).lower()
            if query and query not in haystack:
                continue
            if risk != "All" and item.get("risk_level") != risk:
                continue
            rows.append(
                [
                    item.get("setting_control_name"),
                    item.get("category"),
                    item.get("reachability_status"),
                    item.get("risk_level"),
                    item.get("suggested_default_enabled_state"),
                    item.get("suggested_warning_label"),
                ]
            )
        fill_table(self.table, ["Control", "Category", "Reachability", "Risk", "Default", "Warning"], rows)
