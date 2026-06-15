from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.common import fill_controls_table


class CpuTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("CPU controls are complete in the manifest. Edits save desired preset JSON only. No powercfg writes run in Phase 3."))

        status = QGridLayout()
        self.plan_name = QLabel("")
        self.plan_guid = QLabel("")
        self.last_read = QLabel("")
        self.source = QLabel("")
        for row, (name, label) in enumerate([
            ("Active plan name", self.plan_name),
            ("Active plan GUID", self.plan_guid),
            ("Last read timestamp", self.last_read),
            ("Source", self.source),
        ]):
            status.addWidget(QLabel(name), row, 0)
            status.addWidget(label, row, 1)
        layout.addLayout(status)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter, 1)

        controls_panel = QWidget()
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.addWidget(QLabel("Full CPU control table"))
        self.control_table = QTableWidget()
        controls_layout.addWidget(self.control_table, 1)
        splitter.addWidget(controls_panel)

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.addWidget(QLabel("Preset editor: saves only to presets/cpu_presets.json"))
        top = QHBoxLayout()
        self.preset_box = QComboBox()
        self.preset_box.currentIndexChanged.connect(self.load_selected_preset)
        top.addWidget(QLabel("Preset"))
        top.addWidget(self.preset_box)
        save = QPushButton("Save CPU Preset JSON")
        save.clicked.connect(self.save_preset)
        preview = QPushButton("Preview Dry-run Commands")
        preview.clicked.connect(self.preview_commands)
        top.addWidget(save)
        top.addWidget(preview)
        top.addStretch(1)
        editor_layout.addLayout(top)
        self.preset_table = QTableWidget()
        editor_layout.addWidget(self.preset_table, 1)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        editor_layout.addWidget(self.preview, 1)
        splitter.addWidget(editor_panel)

        self.load_status()
        self.load_controls()
        self.load_preset_names()

    def load_status(self) -> None:
        active = self.window.power.active_scheme()
        self.plan_name.setText(str(active.get("name") or self.window.phase1.summary().get("active_power_plan")))
        self.plan_guid.setText(str(active.get("guid") or self.window.phase1.summary().get("active_power_plan_guid")))
        self.last_read.setText(str(active.get("command", {}).get("started_at") or "Phase 1 fallback"))
        self.source.setText(str(active.get("source", "live powercfg if available")))

    def load_controls(self) -> None:
        rows = [c for c in self.surface.by_tab("CPU Presets") if c.get("category", "").startswith("CPU")]
        fill_controls_table(self.control_table, rows)

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
        preset = self.selected_preset()
        settings = list((preset or {}).get("settings", []))
        headers = ["Enabled", "Control ID", "Friendly name", "Alias", "AC desired", "DC desired", "Risk", "Note"]
        self.preset_table.setColumnCount(len(headers))
        self.preset_table.setHorizontalHeaderLabels(headers)
        self.preset_table.setRowCount(len(settings))
        for row, setting in enumerate(settings):
            values = [
                "true" if setting.get("enabled") else "false",
                setting.get("control_id"),
                setting.get("friendly_name"),
                setting.get("alias"),
                setting.get("desired_ac_value"),
                setting.get("desired_dc_value"),
                setting.get("risk"),
                setting.get("phase3_note"),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem("" if value is None else str(value))
                if col not in {0, 4, 5}:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.preset_table.setItem(row, col, item)
        self.preset_table.resizeColumnsToContents()
        self.preview_commands()

    def save_preset(self) -> None:
        preset = self.selected_preset()
        if not preset:
            return
        settings = preset.get("settings", [])
        for row, setting in enumerate(settings):
            enabled_text = (self.preset_table.item(row, 0).text() if self.preset_table.item(row, 0) else "").lower()
            setting["enabled"] = enabled_text in {"true", "1", "yes", "enabled"}
            setting["desired_ac_value"] = self._cell_value(row, 4)
            setting["desired_dc_value"] = self._cell_value(row, 5)
        path = self.surface.save_cpu_presets()
        QMessageBox.information(self, "Preset saved", f"Saved desired values only:\n{path}")

    def preview_commands(self) -> None:
        preset = self.selected_preset()
        if not preset:
            self.preview.setPlainText("")
            return
        active_guid = self.window.phase1.summary().get("active_power_plan_guid") or "<scheme_guid>"
        lines = [
            "DRY-RUN COMMAND PREVIEW ONLY",
            "Not executed. Requires backup first. Future Phase 4 or later.",
            "",
        ]
        for setting in preset.get("settings", []):
            if not setting.get("enabled"):
                continue
            control = self.surface.find_control(setting.get("control_id"))
            if not control or not control.get("setting_guid"):
                continue
            for side, value_key in [("AC", "desired_ac_value"), ("DC", "desired_dc_value")]:
                value = setting.get(value_key)
                if value in (None, ""):
                    continue
                switch = "/setacvalueindex" if side == "AC" else "/setdcvalueindex"
                lines.append(f"powercfg {switch} {active_guid} SUB_PROCESSOR {control.get('setting_guid')} {value}")
                lines.append(f"  risk={control.get('risk', {}).get('level')} backup_required=true")
        self.preview.setPlainText("\n".join(lines))

    def _cell_value(self, row: int, col: int):
        item = self.preset_table.item(row, col)
        if not item:
            return None
        text = item.text().strip()
        if text == "":
            return None
        try:
            return int(text)
        except ValueError:
            return text
