from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from app.ui.common import fill_controls_table, fill_table


class GpuTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        layout = QVBoxLayout(self)

        status = self.window.msi.status()
        grid = QGridLayout()
        layout.addLayout(grid)
        for row, (label, value) in enumerate([
            ("MSI Afterburner path", status.get("executable_path")),
            ("RTSS path", status.get("rtss_path")),
            ("MSI install folder", status.get("install_folder")),
            ("Profiles folder", status.get("profiles_folder")),
            ("MSI running during Phase 1", status.get("appears_running_phase1")),
            ("Slot mapping verified", "No slots verified in Phase 3"),
        ]):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(QLabel(str(value)), row, 1)

        layout.addWidget(QLabel("MSI profile/config files discovered"))
        files = status.get("profile_files", []) + status.get("config_files", [])
        self.files_table = QTableWidget()
        layout.addWidget(self.files_table, 1)
        fill_table(self.files_table, ["Name", "Path", "Last modified", "Bytes"], [[f.get("name"), f.get("path"), f.get("last_write_local"), f.get("length_bytes")] for f in files])

        layout.addWidget(QLabel("GPU/MSI manifest controls"))
        self.controls_table = QTableWidget()
        layout.addWidget(self.controls_table, 1)
        fill_controls_table(self.controls_table, self.surface.by_tab("GPU Profiles"))

        layout.addWidget(QLabel("Editable slot mapping: saves only to presets/gpu_profiles.json"))
        self.slot_table = QTableWidget()
        layout.addWidget(self.slot_table, 1)
        self.load_slots()

        buttons = QHBoxLayout()
        save = QPushButton("Save Slot Mapping JSON")
        save.clicked.connect(self.save_slots)
        buttons.addWidget(save)
        for slot in range(1, 6):
            button = QPushButton(f"Preview Slot {slot}")
            button.clicked.connect(lambda checked=False, s=slot: self.preview_slot(s))
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        checklist = QTextEdit()
        checklist.setReadOnly(True)
        checklist.setPlainText(
            "\n".join(
                [
                    "Manual verification checklist:",
                    "1. Back up MSI configs/profiles.",
                    "2. Record current telemetry.",
                    "3. Confirm current slot label inside MSI.",
                    "4. Launch manually outside app or in a future guarded phase.",
                    "5. Confirm telemetry change.",
                    "6. Record result.",
                    "7. Mark slot verified only after explicit confirmation in a future phase.",
                ]
            )
        )
        layout.addWidget(checklist)

    def load_slots(self) -> None:
        headers = ["Slot", "Friendly name", "Intended purpose", "Verified", "Last verified", "Expected behavior", "Risk", "Notes"]
        slots = self.surface.gpu_profiles.get("slots", [])
        self.slot_table.setColumnCount(len(headers))
        self.slot_table.setHorizontalHeaderLabels(headers)
        self.slot_table.setRowCount(len(slots))
        for row, slot in enumerate(slots):
            values = [
                slot.get("slot"),
                slot.get("friendly_name"),
                slot.get("intended_purpose"),
                slot.get("verified"),
                slot.get("last_verified_timestamp"),
                slot.get("expected_behavior"),
                slot.get("risk"),
                slot.get("notes"),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                if col in {0, 3, 6}:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.slot_table.setItem(row, col, item)
        self.slot_table.resizeColumnsToContents()

    def save_slots(self) -> None:
        slots = self.surface.gpu_profiles.get("slots", [])
        for row, slot in enumerate(slots):
            slot["friendly_name"] = self._text(row, 1)
            slot["intended_purpose"] = self._text(row, 2)
            slot["last_verified_timestamp"] = self._text(row, 4) or None
            slot["expected_behavior"] = self._text(row, 5)
            slot["notes"] = self._text(row, 7)
        path = self.surface.save_gpu_profiles()
        QMessageBox.information(self, "Slot mapping saved", f"Saved app-side labels only:\n{path}")

    def preview_slot(self, slot: int) -> None:
        control = self.surface.find_control(f"gpu.msi.profile.slot{slot}")
        if not control:
            return
        QMessageBox.warning(self, f"Profile {slot} dry-run", self.surface.dry_run_preview_for(control))

    def _text(self, row: int, col: int) -> str:
        item = self.slot_table.item(row, col)
        return item.text().strip() if item else ""
