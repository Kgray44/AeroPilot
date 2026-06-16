from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableWidget, QTextEdit, QVBoxLayout, QWidget

from app.ui.common import fill_controls_table, fill_table


class FanExperimentalTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Experimental/read-only. Fan control, service control, config writes, and embedded-controller writes are blocked in Phase 5."))
        status = window.gigabyte.status()

        layout.addWidget(QLabel("Fan/OEM manifest entries"))
        self.controls = QTableWidget()
        fill_controls_table(self.controls, self.surface.by_tab("Fan Control / Experimental"))
        layout.addWidget(self.controls, 1)

        layout.addWidget(QLabel("Gigabyte/GCC running processes from Phase 1"))
        self.processes = QTableWidget()
        layout.addWidget(self.processes)
        fill_table(self.processes, ["Process", "PID", "Path"], [[p.get("process_name"), p.get("id"), p.get("path")] for p in status.get("running_processes", [])])

        layout.addWidget(QLabel("Relevant services from Phase 1"))
        self.services = QTableWidget()
        layout.addWidget(self.services)
        fill_table(self.services, ["Name", "Display", "State", "Start mode", "Path"], [[s.get("name"), s.get("display_name"), s.get("state"), s.get("start_mode"), s.get("path_name")] for s in status.get("services", [])])

        layout.addWidget(QLabel("Fan control feasibility"))
        self.feasibility = QTableWidget()
        layout.addWidget(self.feasibility)
        fill_table(self.feasibility, ["Method", "Likelihood", "Phase 1 status", "Risk"], [[f.get("method"), f.get("likelihood"), f.get("phase1_status"), f.get("risk")] for f in status.get("fan_control_feasibility", [])])

        blocked = QTextEdit()
        blocked.setReadOnly(True)
        blocked.setPlainText(
            "\n".join(
                [
                    "Blocked actions:",
                    "- Change fan mode through GCC: blocked until official reversible path is proven.",
                    "- Stop/start GCC services: blocked; service control is outside Phase 3.",
                    "- Direct embedded-controller access: blocked as dangerous/research-only.",
                    "- Fan curve editing: blocked until backup/restore and evidence exist.",
                    "",
                    "Unlock evidence required: official API or reversible command path, current-state capture, restore proof, manual confirmation, and panic restore design.",
                ]
            )
        )
        layout.addWidget(blocked)
