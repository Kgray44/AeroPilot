from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTextEdit, QWidget

from app.core.config_loader import load_json
from app.ui.common import add_form_row, make_badge, make_card, make_metric, make_page_header, make_scroll_page


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

        layout, _body = make_scroll_page(self)
        gates = load_json(self.window.paths.config_dir / "apply_gate_config.json", {})
        sandbox = load_json(self.window.paths.phase4_root / "sandbox" / "sandbox_powercfg_test_result.json", {})
        layout.addWidget(
            make_page_header(
                "CPU Presets",
                "Edit desired CPU preset values in app-side JSON. Active-plan writes remain locked; dry-run previews show future commands only.",
                [("Active plan protected", "safe"), ("Sandbox writes only", "neutral")],
            )
        )

        active = self.window.power.active_scheme()
        metrics = QHBoxLayout()
        metric_panel = QWidget()
        metric_panel.setLayout(metrics)
        metrics.addWidget(make_metric("Active plan", str(active.get("name") or self.window.phase1.summary().get("active_power_plan"))))
        metrics.addWidget(make_metric("Sandbox test", "Passed" if sandbox.get("passed") else "Not passed", "safe" if sandbox.get("passed") else "warn"))
        metrics.addWidget(make_metric("Active writes", str(gates.get("active_plan_write_enabled", False)), "warn"))
        metrics.addStretch(1)
        layout.addWidget(metric_panel)

        chooser_card, chooser_layout = make_card("Preset", "Choose a preset, edit its desired values, then save JSON. Nothing is applied to Windows.")
        row = QHBoxLayout()
        self.preset_box = QComboBox()
        self.preset_box.currentIndexChanged.connect(self.load_selected_preset)
        row.addWidget(self.preset_box, 1)
        save = QPushButton("Save CPU Preset JSON")
        save.clicked.connect(self.save_preset)
        preview = QPushButton("Refresh Dry-run Preview")
        preview.clicked.connect(self.preview_commands)
        row.addWidget(save)
        row.addWidget(preview)
        chooser_layout.addLayout(row)
        layout.addWidget(chooser_card)

        editor_card, editor_layout = make_card("Desired CPU Settings", "Every setting is editable here as desired state only. Dropdowns are used where Windows exposes a small known option set.")
        self.editor_container = QWidget()
        self.editor_container.setObjectName("cpu_setting_editor")
        self.editor_layout = QHBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self.editor_container)
        layout.addWidget(editor_card)

        preview_card, preview_layout = make_card("Dry-run command preview", "These commands are not executed in this phase.")
        self.preview = QTextEdit()
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

    def load_selected_preset(self) -> None:
        while self.editor_layout.count():
            item = self.editor_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.setting_widgets = []

        preset = self.selected_preset()
        if not preset:
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

        for index, setting in enumerate(preset.get("settings", [])):
            card, card_layout = make_card(setting.get("friendly_name") or setting.get("control_id"), f"{setting.get('alias')} | Risk: {setting.get('risk')}")
            enabled = QCheckBox("Enabled in preset")
            enabled.setChecked(bool(setting.get("enabled")))
            card_layout.addWidget(enabled)
            ac_widget = self._value_widget(setting, "desired_ac_value", "ac")
            dc_widget = self._value_widget(setting, "desired_dc_value", "dc")
            add_form_row(card_layout, "AC desired value", ac_widget, "Saved to preset JSON only.")
            add_form_row(card_layout, "DC desired value", dc_widget, "Saved to preset JSON only.")
            note = QLabel(setting.get("phase3_note") or "Preview-only desired value.")
            note.setWordWrap(True)
            card_layout.addWidget(note)
            column_bodies[index % 2].addWidget(card)
            self.setting_widgets.append({"setting": setting, "enabled": enabled, "ac": ac_widget, "dc": dc_widget})

        for body in column_bodies:
            body.addStretch(1)
        self.editor_layout.addWidget(columns[0], 1)
        self.editor_layout.addWidget(columns[1], 1)
        self.preview_commands()

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

    def save_preset(self) -> None:
        for row in self.setting_widgets:
            setting = row["setting"]
            setting["enabled"] = row["enabled"].isChecked()
            setting["desired_ac_value"] = self._read_widget(row["ac"])
            setting["desired_dc_value"] = self._read_widget(row["dc"])
        path = self.surface.save_cpu_presets()
        QMessageBox.information(self, "Preset saved", f"Saved desired values only:\n{path}")
        self.preview_commands()

    def preview_commands(self) -> None:
        preset = self.selected_preset()
        if not preset:
            self.preview.setPlainText("")
            return
        active_guid = self.window.phase1.summary().get("active_power_plan_guid") or "<scheme_guid>"
        lines = ["DRY-RUN COMMAND PREVIEW ONLY", "Not executed. Future active-plan apply remains locked.", ""]
        for row in self.setting_widgets:
            setting = row["setting"]
            if not row["enabled"].isChecked():
                continue
            control = self.surface.find_control(setting.get("control_id"))
            if not control or not control.get("setting_guid"):
                continue
            for side, widget in [("AC", row["ac"]), ("DC", row["dc"])]:
                value = self._read_widget(widget)
                if value in (None, ""):
                    continue
                switch = "/setacvalueindex" if side == "AC" else "/setdcvalueindex"
                lines.append(f"powercfg {switch} {active_guid} SUB_PROCESSOR {control.get('setting_guid')} {value}")
                lines.append(f"  risk={control.get('risk', {}).get('level')} backup_required=true preview_only=true")
        self.preview.setPlainText("\n".join(lines))

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
