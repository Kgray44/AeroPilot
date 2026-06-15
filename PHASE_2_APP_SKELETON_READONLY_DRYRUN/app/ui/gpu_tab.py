from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QVBoxLayout, QWidget

from app.ui.common import fill_table


class GpuTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        status = self.window.msi.status()
        grid = QGridLayout()
        layout.addLayout(grid)
        for row, (label, value) in enumerate(
            [
                ("MSI Afterburner path", status.get("executable_path")),
                ("RTSS path", status.get("rtss_path")),
                ("MSI install folder", status.get("install_folder")),
                ("Profiles folder", status.get("profiles_folder")),
                ("MSI running during Phase 1", status.get("appears_running_phase1")),
            ]
        ):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(QLabel(str(value)), row, 1)

        layout.addWidget(QLabel("Config/profile files found"))
        files = status.get("profile_files", []) + status.get("config_files", [])
        self.files_table = QTableWidget()
        layout.addWidget(self.files_table, 1)
        fill_table(self.files_table, ["Name", "Path", "Last modified"], [[f.get("name"), f.get("path"), f.get("last_write_local")] for f in files])

        layout.addWidget(QLabel("MSI profile slots. All mappings are unverified by default."))
        self.slot_table = QTableWidget()
        layout.addWidget(self.slot_table)
        fill_table(
            self.slot_table,
            ["Slot", "Friendly name", "Verified", "Risk", "Warning"],
            [[s["slot"], s["friendly_name"], s["verified"], s["risk"], s["warning"]] for s in self.window.msi.slots()],
        )

        button_grid = QGridLayout()
        layout.addLayout(button_grid)
        for index in range(1, 6):
            button = QPushButton(f"Preview MSI Profile {index} Command")
            button.clicked.connect(lambda checked=False, slot=index: self.preview_slot(slot))
            button_grid.addWidget(button, (index - 1) // 2, (index - 1) % 2)

    def preview_slot(self, slot: int) -> None:
        preview = self.window.msi.preview_profile_command(slot)
        QMessageBox.warning(
            self,
            f"Profile {slot} dry-run",
            preview.command_line()
            + "\n\nWrong slot may apply an unintended GPU curve."
            + "\nBackup is required before any future profile launch test."
            + "\nPhase 3 must manually verify slot mapping."
            + "\n\n"
            + preview.phase2_reason_not_executed,
        )
