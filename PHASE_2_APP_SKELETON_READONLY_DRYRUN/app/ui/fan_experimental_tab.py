from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableWidget, QVBoxLayout, QWidget

from app.ui.common import fill_table


class FanExperimentalTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Experimental/read-only. No fan apply button exists in Phase 2."))
        status = window.gigabyte.status()

        self.entries = QTableWidget()
        layout.addWidget(QLabel("Gigabyte installed entries"))
        layout.addWidget(self.entries)
        fill_table(self.entries, ["Name", "Version", "Publisher"], [[e.get("display_name"), e.get("display_version"), e.get("publisher")] for e in status.get("installed_entries", [])])

        self.services = QTableWidget()
        layout.addWidget(QLabel("Relevant services from Phase 1"))
        layout.addWidget(self.services)
        fill_table(self.services, ["Name", "Display", "State", "Start mode", "Path"], [[s.get("name"), s.get("display_name"), s.get("state"), s.get("start_mode"), s.get("path_name")] for s in status.get("services", [])])

        self.feasibility = QTableWidget()
        layout.addWidget(QLabel("Fan control feasibility"))
        layout.addWidget(self.feasibility, 1)
        fill_table(self.feasibility, ["Method", "Likelihood", "Phase 1 status", "Risk"], [[f.get("method"), f.get("likelihood"), f.get("phase1_status"), f.get("risk")] for f in status.get("fan_control_feasibility", [])])

        layout.addWidget(QLabel("Official API: unknown | Command-line control: unknown | Config-file control: unproven | UI automation: possible but fragile | Embedded controller writes: dangerous/research only"))
