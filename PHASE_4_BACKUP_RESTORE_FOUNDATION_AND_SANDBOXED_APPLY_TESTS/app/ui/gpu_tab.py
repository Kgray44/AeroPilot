from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTextEdit, QWidget

from app.core.config_loader import load_json
from app.ui.common import add_form_row, fill_table, make_card, make_metric, make_page_header, make_scroll_page


PURPOSE_OPTIONS = ["Unverified", "Stock", "Quiet", "Gaming Balanced", "BF6 Emergency", "Benchmark", "Custom"]
RISK_OPTIONS = ["Low", "Medium", "High", "Dangerous / Experimental", "Unknown"]


class GpuTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        self.slot_widgets: list[dict] = []
        layout, _body = make_scroll_page(self)
        gates = load_json(self.window.paths.config_dir / "apply_gate_config.json", {})
        msi_manifest = load_json(self.window.paths.phase4_root / "backups" / "msi_afterburner" / "msi_backup_manifest.json", {})
        status = self.window.msi.status()

        layout.addWidget(
            make_page_header(
                "GPU Profiles",
                "Edit friendly MSI slot metadata and preview launch commands. AeroTune still refuses to execute MSI profile launches.",
                [("MSI launch blocked", "safe"), ("Slot mapping unverified", "warn")],
            )
        )

        metrics = QHBoxLayout()
        metric_panel = QWidget()
        metric_panel.setLayout(metrics)
        metrics.addWidget(make_metric("MSI backup", str(gates.get("msi_configs_backed_up", False)), "safe" if gates.get("msi_configs_backed_up") else "warn"))
        metrics.addWidget(make_metric("Files backed up", str(len(msi_manifest.get("copied_files", [])))))
        metrics.addWidget(make_metric("Profile apply", str(gates.get("msi_profile_apply_enabled", False)), "warn"))
        metrics.addStretch(1)
        layout.addWidget(metric_panel)

        info_card, info_layout = make_card("MSI Afterburner reachability", "Discovered paths are read-only reference data.")
        info_lines = [
            ("MSI Afterburner path", status.get("executable_path")),
            ("RTSS path", status.get("rtss_path")),
            ("MSI install folder", status.get("install_folder")),
            ("Profiles folder", status.get("profiles_folder")),
            ("MSI running during Phase 1", status.get("appears_running_phase1")),
        ]
        for label, value in info_lines:
            add_form_row(info_layout, label, QLabel(str(value)), None)
        layout.addWidget(info_card)

        slot_card, slot_layout = make_card("Editable slot mapping", "These fields save to presets/gpu_profiles.json only. Marking a slot verified here does not enable MSI launching.")
        self.slot_editor = QWidget()
        self.slot_editor.setObjectName("gpu_slot_editor")
        self.slot_layout = QHBoxLayout(self.slot_editor)
        self.slot_layout.setContentsMargins(0, 0, 0, 0)
        slot_layout.addWidget(self.slot_editor)
        layout.addWidget(slot_card)
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

        files_card, files_layout = make_card("Discovered MSI files", "Read-only file list from discovery and backup.")
        files = status.get("profile_files", []) + status.get("config_files", [])
        self.files_table = QTableWidget()
        files_layout.addWidget(self.files_table)
        fill_table(self.files_table, ["Name", "Path", "Last modified", "Bytes"], [[f.get("name"), f.get("path"), f.get("last_write_local"), f.get("length_bytes")] for f in files])
        layout.addWidget(files_card)

        checklist_card, checklist_layout = make_card("Phase 5 verification checklist")
        checklist = QTextEdit()
        checklist.setReadOnly(True)
        checklist.setPlainText(
            "\n".join(
                [
                    "1. Confirm MSI backup exists.",
                    "2. Record current telemetry.",
                    "3. Verify one slot manually with telemetry.",
                    "4. Record observed behavior.",
                    "5. Only then consider enabling guarded app launch in a future phase.",
                ]
            )
        )
        checklist_layout.addWidget(checklist)
        layout.addWidget(checklist_card)
        layout.addStretch(1)

    def load_slots(self) -> None:
        while self.slot_layout.count():
            item = self.slot_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.slot_widgets = []
        from PySide6.QtWidgets import QVBoxLayout

        columns = [QWidget(), QWidget()]
        bodies = []
        for column in columns:
            body = QVBoxLayout()
            body.setContentsMargins(0, 0, 0, 0)
            body.setSpacing(12)
            column.setLayout(body)
            bodies.append(body)

        for index, slot in enumerate(self.surface.gpu_profiles.get("slots", [])):
            card, card_layout = make_card(f"Slot {slot.get('slot')}", "Metadata only. Launch remains blocked.")
            friendly = QLineEdit(str(slot.get("friendly_name") or ""))
            purpose = QComboBox()
            purpose.addItems(PURPOSE_OPTIONS)
            purpose.setCurrentText(str(slot.get("intended_purpose") or "Unverified"))
            verified = QCheckBox("Verified by manual telemetry")
            verified.setChecked(bool(slot.get("verified")))
            verified.setToolTip("Saving this checkbox does not enable MSI profile launching.")
            last_verified = QLineEdit("" if slot.get("last_verified_timestamp") is None else str(slot.get("last_verified_timestamp")))
            expected = QLineEdit(str(slot.get("expected_behavior") or ""))
            risk = QComboBox()
            risk.addItems(RISK_OPTIONS)
            risk.setCurrentText(str(slot.get("risk") or "Medium"))
            notes = QLineEdit(str(slot.get("notes") or ""))
            add_form_row(card_layout, "Friendly name", friendly)
            add_form_row(card_layout, "Intended purpose", purpose)
            card_layout.addWidget(verified)
            add_form_row(card_layout, "Last verified", last_verified, "Optional timestamp or short note.")
            add_form_row(card_layout, "Expected behavior", expected)
            add_form_row(card_layout, "Risk", risk)
            add_form_row(card_layout, "Notes", notes)
            bodies[index % 2].addWidget(card)
            self.slot_widgets.append({"slot": slot, "friendly": friendly, "purpose": purpose, "verified": verified, "last": last_verified, "expected": expected, "risk": risk, "notes": notes})

        for body in bodies:
            body.addStretch(1)
        self.slot_layout.addWidget(columns[0], 1)
        self.slot_layout.addWidget(columns[1], 1)

    def save_slots(self) -> None:
        for row in self.slot_widgets:
            slot = row["slot"]
            slot["friendly_name"] = row["friendly"].text().strip()
            slot["intended_purpose"] = row["purpose"].currentText()
            slot["verified"] = row["verified"].isChecked()
            slot["last_verified_timestamp"] = row["last"].text().strip() or None
            slot["expected_behavior"] = row["expected"].text().strip()
            slot["risk"] = row["risk"].currentText()
            slot["notes"] = row["notes"].text().strip()
        path = self.surface.save_gpu_profiles()
        QMessageBox.information(self, "Slot mapping saved", f"Saved app-side labels only:\n{path}")

    def preview_slot(self, slot: int) -> None:
        control = self.surface.find_control(f"gpu.msi.profile.slot{slot}")
        if not control:
            return
        QMessageBox.warning(self, f"Profile {slot} dry-run", self.surface.dry_run_preview_for(control))
