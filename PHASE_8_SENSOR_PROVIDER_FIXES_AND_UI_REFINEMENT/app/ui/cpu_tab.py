from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSizePolicy, QSpinBox, QWidget

from app.core.config_loader import load_json
from app.ui.common import add_form_row, make_badge, make_card, make_page_header, make_scroll_page


BOOST_MODE_OPTIONS = {
    0: "Disabled",
    1: "Enabled",
    2: "Aggressive",
    3: "Efficient Enabled",
    4: "Efficient Aggressive",
    5: "Aggressive At Guaranteed",
    6: "Efficient Aggressive At Guaranteed",
}
COOLING_OPTIONS = {0: "Passive", 1: "Active"}


class CpuTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        self.setting_widgets: list[dict] = []
        self.selected_power_source = "AC"
        self._loading = False
        self.current_values = self.window.power.current_values_by_control(self.window.paths)

        layout, _body = make_scroll_page(self)
        layout.addWidget(
            make_page_header(
                "CPU Presets",
                "Edit desired CPU preset values by power source. Active-plan writes remain blocked until backup and restore gates are proven.",
                [("Active plan protected", "safe"), ("Phase 5 guarded foundation", "neutral")],
            )
        )

        top_card, top_layout = make_card("Preset and power source", "Choose one power source view at a time. Switching AC/DC saves visible edits in memory before rebuilding.")
        chooser_row = QHBoxLayout()
        self.preset_box = QComboBox()
        self.preset_box.setMaximumHeight(42)
        self.preset_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.preset_box.currentIndexChanged.connect(lambda _index: self.load_selected_preset())
        self.power_source_box = QComboBox()
        self.power_source_box.setObjectName("cpu_power_source_selector")
        self.power_source_box.setMaximumHeight(42)
        self.power_source_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.power_source_box.addItems(["AC", "DC"])
        self.power_source_box.currentTextChanged.connect(self.change_power_source)
        chooser_row.addWidget(QLabel("Preset"))
        chooser_row.addWidget(self.preset_box, 2)
        chooser_row.addWidget(QLabel("Power source view"))
        chooser_row.addWidget(self.power_source_box)
        top_layout.addLayout(chooser_row)

        self.summary_row = QHBoxLayout()
        top_layout.addLayout(self.summary_row)
        self.apply_gate_status = QLabel()
        self.apply_gate_status.setObjectName("cpu_apply_gate_status")
        self.apply_gate_status.setWordWrap(True)
        top_layout.addWidget(self.apply_gate_status)
        self.diff_summary = QLabel()
        self.diff_summary.setObjectName("cpu_current_vs_desired_summary")
        self.diff_summary.setWordWrap(True)
        top_layout.addWidget(self.diff_summary)
        layout.addWidget(top_card)

        buttons = QHBoxLayout()
        for text, callback in [
            ("Refresh Current Values", self.refresh_current_values),
            ("Save CPU Preset JSON", self.save_preset),
            ("Refresh Dry-run Preview", self.preview_commands),
            ("Check Apply Gates", self.check_apply_gates),
            ("Preview Guarded Apply", self.preview_guarded_apply),
            ("Restore Preview", self.restore_preview),
        ]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        self.real_apply = QPushButton("Real Apply Locked")
        self.real_apply.setObjectName("cpu_guarded_apply_button")
        self.real_apply.setEnabled(False)
        buttons.addWidget(self.real_apply)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        editor_card, editor_layout = make_card("Desired CPU Settings", "Only the selected AC or DC desired value is visible. Tables are avoided here; each setting is edited as a compact card.")
        self.editor_container = QWidget()
        self.editor_container.setObjectName("cpu_setting_editor")
        self.editor_layout = QHBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self.editor_container)
        layout.addWidget(editor_card)

        preview_card, preview_layout = make_card("Selected-side dry-run preview", "These commands are not executed. The preview only shows the selected AC/DC side.")
        self.preview = QPlainTextEdit()
        self.preview.setObjectName("cpu_dryrun_preview")
        self.preview.setReadOnly(True)
        self.preview.setMinimumHeight(220)
        preview_layout.addWidget(self.preview)
        layout.addWidget(preview_card)
        layout.addStretch(1)
        self.load_preset_names()

    def load_preset_names(self) -> None:
        self.preset_box.blockSignals(True)
        self.preset_box.clear()
        for preset in self.surface.cpu_presets.get("presets", []):
            self.preset_box.addItem(preset.get("name", "Unnamed"))
        self.preset_box.blockSignals(False)
        self.load_selected_preset()

    def selected_preset(self) -> dict | None:
        index = self.preset_box.currentIndex()
        presets = self.surface.cpu_presets.get("presets", [])
        if 0 <= index < len(presets):
            return presets[index]
        return None

    def change_power_source(self, value: str) -> None:
        if self._loading:
            return
        self._capture_visible_edits()
        self.selected_power_source = value
        self.load_selected_preset(capture=False)

    def load_selected_preset(self, capture: bool = True) -> None:
        if capture:
            self._capture_visible_edits()
        self._loading = True
        while self.editor_layout.count():
            item = self.editor_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        self.setting_widgets = []

        preset = self.selected_preset()
        if not preset:
            self._loading = False
            return
        from PySide6.QtWidgets import QVBoxLayout

        columns = [QWidget(), QWidget()]
        column_bodies = []
        for column in columns:
            body = QVBoxLayout()
            body.setContentsMargins(0, 0, 0, 0)
            body.setSpacing(12)
            column.setLayout(body)
            column_bodies.append(body)

        desired_key = self._desired_key()
        for index, setting in enumerate(preset.get("settings", [])):
            current = self.current_values.get(setting.get("control_id"), {})
            status = self._diff_status(setting, current)
            card, card_layout = make_card(
                setting.get("friendly_name") or setting.get("control_id"),
                f"{setting.get('alias') or setting.get('control_id')} | Risk: {setting.get('risk')} | {status}",
            )
            enabled = QCheckBox("Enabled in preset")
            enabled.setChecked(bool(setting.get("enabled")))
            card_layout.addWidget(enabled)

            current_label = QLabel(f"Current {self.selected_power_source}: {self._current_display(current)}")
            current_label.setTextInteractionFlags(current_label.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse)
            card_layout.addWidget(current_label)

            desired_widget = self._value_widget(setting, desired_key, self.selected_power_source.lower())
            desired_widget.setObjectName(f"cpu_desired_{self.selected_power_source.lower()}_value_editor")
            add_form_row(card_layout, f"{self.selected_power_source} desired value", desired_widget, "Saved to preset JSON only.")

            restore = QLabel(self._restore_status(setting))
            restore.setWordWrap(True)
            card_layout.addWidget(restore)
            lock = QLabel("Status: preview-only / active apply blocked")
            lock.setWordWrap(True)
            card_layout.addWidget(lock)
            column_bodies[index % 2].addWidget(card)
            self.setting_widgets.append({"setting": setting, "enabled": enabled, "value": desired_widget, "status": status})

        for body in column_bodies:
            body.addStretch(1)
        self.editor_layout.addWidget(columns[0], 1)
        self.editor_layout.addWidget(columns[1], 1)
        self._loading = False
        self.preview_commands()
        self.update_summary()

    def _desired_key(self) -> str:
        return "desired_ac_value" if self.selected_power_source == "AC" else "desired_dc_value"

    def _current_key(self) -> str:
        return "ac_value" if self.selected_power_source == "AC" else "dc_value"

    def _value_widget(self, setting: dict, key: str, side: str):
        control_id = setting.get("control_id")
        value = setting.get(key)
        if control_id == "cpu.boost.mode":
            widget = QComboBox()
            widget.setObjectName(f"cpu_boost_mode_{side}_editor")
            self._populate_option_box(widget, BOOST_MODE_OPTIONS, value)
            return widget
        if control_id == "cpu.cooling.system_policy":
            widget = QComboBox()
            widget.setObjectName(f"cpu_cooling_policy_{side}_editor")
            self._populate_option_box(widget, COOLING_OPTIONS, value)
            return widget
        if isinstance(value, int):
            widget = QSpinBox()
            widget.setRange(0, 100000)
            widget.setValue(value)
            return widget
        widget = QLineEdit("" if value is None else str(value))
        widget.setPlaceholderText("blank / not set")
        return widget

    def _populate_option_box(self, widget: QComboBox, options: dict[int, str], value) -> None:
        for number, label in options.items():
            widget.addItem(f"{number} - {label}", number)
        current = widget.findData(value)
        if current >= 0:
            widget.setCurrentIndex(current)

    def _capture_visible_edits(self) -> None:
        key = self._desired_key()
        for row in getattr(self, "setting_widgets", []):
            row["setting"]["enabled"] = row["enabled"].isChecked()
            row["setting"][key] = self._read_widget(row["value"])

    def save_preset(self) -> None:
        self._capture_visible_edits()
        path = self.surface.save_cpu_presets()
        QMessageBox.information(self, "Preset saved", f"Saved desired values only:\n{path}")
        self.preview_commands()

    def refresh_current_values(self) -> None:
        self.current_values = self.window.power.current_values_by_control(self.window.paths)
        self.load_selected_preset(capture=True)

    def preview_commands(self) -> None:
        self._capture_visible_edits()
        preset = self.selected_preset()
        if not preset:
            self.preview.setPlainText("")
            return
        active = self.window.power.active_scheme()
        active_guid = active.get("guid") or self.window.phase1.summary().get("active_power_plan_guid") or "<scheme_guid>"
        switch = "/setacvalueindex" if self.selected_power_source == "AC" else "/setdcvalueindex"
        lines = [
            "DRY-RUN COMMAND PREVIEW ONLY",
            f"Selected {self.selected_power_source} command set only.",
            "Not executed. Active-plan CPU apply remains blocked until all gates pass.",
            "",
        ]
        count = 0
        for row in self.setting_widgets:
            setting = row["setting"]
            if not row["enabled"].isChecked():
                continue
            control = self.surface.find_control(setting.get("control_id"))
            setting_guid = setting.get("setting_guid") or (control or {}).get("setting_guid")
            if not setting_guid:
                continue
            value = self._read_widget(row["value"])
            if value in (None, ""):
                continue
            count += 1
            lines.append(f"powercfg {switch} {active_guid} SUB_PROCESSOR {setting_guid} {value}")
            lines.append(f"  control={setting.get('control_id')} risk={setting.get('risk')} backup_required=true phase5_preview_only=true")
        if count == 0:
            lines.append(f"Selected {self.selected_power_source} command set: no enabled settings with desired values.")
        self.preview.setPlainText("\n".join(lines))
        self.update_summary()

    def check_apply_gates(self) -> None:
        self.update_summary()
        QMessageBox.information(self, "Apply gates", self.apply_gate_status.text())

    def preview_guarded_apply(self) -> None:
        self.preview_commands()
        QMessageBox.information(self, "Guarded apply preview", "Phase 5 builds the preview/foundation only. Real active-plan apply is disabled until backup/export and restore gates pass.")

    def restore_preview(self) -> None:
        self._capture_visible_edits()
        QMessageBox.information(self, "Restore preview", "Restore remains preview-only in Phase 5. See restore/generated_scripts for generated preview scripts after running Phase 5 backup scripts.")

    def update_summary(self) -> None:
        while self.summary_row.count():
            item = self.summary_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        preset = self.selected_preset() or {}
        active = self.window.power.active_scheme()
        gates = load_json(self.window.paths.config_dir / "apply_gate_config.json", {})
        sandbox = load_json(self.window.paths.phase4_root / "sandbox" / "sandbox_powercfg_test_result.json", {})
        enabled = [row for row in self.setting_widgets if row["enabled"].isChecked()]
        would_change = [row for row in self.setting_widgets if row["enabled"].isChecked() and row.get("status") == "would change"]
        chips = [
            (f"Preset: {preset.get('name', 'None')}", "neutral"),
            (f"Power: {self.selected_power_source}", "neutral"),
            (f"Active plan: {active.get('name') or 'unknown'}", "strong"),
            (f"Backup export: {gates.get('active_power_plan_exported', False)}", "safe" if gates.get("active_power_plan_exported") else "warn"),
            ("Sandbox: Passed" if sandbox.get("passed") else "Sandbox: Not passed", "safe" if sandbox.get("passed") else "warn"),
            ("CPU apply: Blocked" if not gates.get("cpu_guarded_apply_enabled") else "CPU apply: Foundation ready", "warn"),
            (f"Enabled: {len(enabled)}", "neutral"),
            (f"Would change: {len(would_change)}", "warn" if would_change else "safe"),
        ]
        for text, tone in chips:
            chip = make_badge(text, tone)
            chip.setMaximumHeight(34)
            self.summary_row.addWidget(chip)
        self.summary_row.addStretch(1)
        blockers = []
        for key in ["active_power_plan_exported", "current_values_snapshot_exists", "restore_manifest_exists", "sandbox_powercfg_write_test_passed", "cpu_guarded_apply_enabled", "active_plan_write_enabled"]:
            if not gates.get(key, False):
                blockers.append(key)
        self.apply_gate_status.setText("Active CPU apply blocked by: " + ", ".join(blockers) if blockers else "All CPU apply gates are satisfied, but broad apply remains disabled by Phase 5 policy.")
        self.diff_summary.setText(f"{self.selected_power_source}: {len(enabled)} enabled settings visible, {len(would_change)} would change.")

    def _read_widget(self, widget):
        if isinstance(widget, QComboBox):
            return widget.currentData()
        if isinstance(widget, QSpinBox):
            return int(widget.value())
        if isinstance(widget, QLineEdit):
            text = widget.text().strip()
            if not text:
                return None
            try:
                return int(text)
            except ValueError:
                return text
        return None

    def _current_display(self, current: dict) -> str:
        if not current or not current.get("readable"):
            return "unreadable"
        value = current.get(self._current_key())
        return "not set" if value is None else str(value)

    def _diff_status(self, setting: dict, current: dict) -> str:
        desired = setting.get(self._desired_key())
        if desired in (None, ""):
            return "desired not set"
        if not current or not current.get("readable"):
            return "current unreadable"
        current_value = current.get(self._current_key())
        if current_value is None:
            return "current unreadable"
        return "matches current" if str(current_value) == str(desired) else "would change"

    def _restore_status(self, setting: dict) -> str:
        current = self.current_values.get(setting.get("control_id"), {})
        if current and current.get("readable"):
            return f"Restore source: captured current {self.selected_power_source} value {current.get(self._current_key())}"
        return "Restore source: unavailable until readable current value is captured."
