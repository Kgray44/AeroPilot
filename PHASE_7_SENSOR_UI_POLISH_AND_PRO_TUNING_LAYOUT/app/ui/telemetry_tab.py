from __future__ import annotations

import time
import threading
from datetime import datetime
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.config_loader import save_json_inside_phase7
from app.core.sensor_presentation import SensorPresentation
from app.ui.common import fill_table, make_card, make_page_header, make_scroll_page
from app.ui.telemetry_widgets import HardwarePanel, HeroMetricCard, MetricChip, SectionHeader, StatusPill


class SensorRefreshSignals(QObject):
    ready = Signal(dict)


class TelemetryTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.surface = window.control_surface
        self.refresh_signals = SensorRefreshSignals()
        self.refresh_signals.ready.connect(self._apply_refresh_payload)
        self.refresh_busy = False
        self.current_model = window.latest_sensor_model
        self.current_presentation: dict[str, Any] = {}
        self.current_raw_rows: list[dict[str, Any]] = []
        self.current_raw_table_rows: list[dict[str, Any]] = []
        self.filtered_raw_rows: list[dict[str, Any]] = []
        self.hero_cards: dict[str, HeroMetricCard] = {}
        self.hardware_panels: dict[str, HardwarePanel] = {}

        self.timer = QTimer(self)
        interval = int(self.surface.app_config.get("polling", {}).get("interval_seconds", 5))
        self.timer.setInterval(max(3, interval) * 1000)
        self.timer.timeout.connect(self.refresh_all)

        layout, self.body = make_scroll_page(self)
        self.scroll_area = self.findChild(QScrollArea)
        layout.addWidget(
            make_page_header(
                "Sensors / Telemetry",
                "A polished read-only telemetry command center for NVIDIA, LibreHardwareMonitor, and opt-in PresentMon.",
                [("Telemetry only", "safe"), ("No auto capture", "neutral"), ("All tuning writes blocked", "warn")],
            )
        )

        self._build_top_controls(layout)
        self._build_hero_strip(layout)
        self._build_mode_buttons(layout)
        self._build_hardware_panels(layout)
        self._build_favorites_section(layout)
        self._build_raw_explorer(layout)
        self._build_cpu_diagnostics(layout)

        if self.surface.app_config.get("polling", {}).get("enabled", False):
            self.timer.start()
        self._render_model(self.current_model)
        self.refresh_all()

    def _build_top_controls(self, layout: QVBoxLayout) -> None:
        panel = QWidget()
        panel.setObjectName("sensor_top_control_bar")
        row = QHBoxLayout(panel)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        refresh = QPushButton("Refresh All")
        refresh.setObjectName("sensor_refresh_button")
        refresh.clicked.connect(self.refresh_all)
        self.pause_button = QPushButton("Pause Live Polling")
        self.pause_button.setObjectName("sensor_pause_resume_button")
        self.pause_button.clicked.connect(self.toggle_polling)
        self.status_label = QLabel("Last refresh: not read yet")
        self.status_label.setObjectName("sensor_refresh_status")
        self.status_label.setWordWrap(True)
        row.addWidget(refresh)
        row.addWidget(self.pause_button)
        row.addWidget(self.status_label, 1)
        layout.addWidget(panel)

        self.status_pills_panel = QWidget()
        self.status_pills_panel.setObjectName("sensor_status_pills")
        self.status_pills_layout = QHBoxLayout(self.status_pills_panel)
        self.status_pills_layout.setContentsMargins(0, 0, 0, 0)
        self.status_pills_layout.setSpacing(8)
        layout.addWidget(self.status_pills_panel)

    def _build_hero_strip(self, layout: QVBoxLayout) -> None:
        layout.addWidget(SectionHeader("Telemetry Overview", "Primary readings first. Sensor count and source state live in compact pills above."))
        self.hero_strip = QWidget()
        self.hero_strip.setObjectName("sensor_hero_strip")
        self.hero_layout = QGridLayout(self.hero_strip)
        self.hero_layout.setContentsMargins(0, 0, 0, 0)
        self.hero_layout.setHorizontalSpacing(14)
        self.hero_layout.setVerticalSpacing(14)
        layout.addWidget(self.hero_strip)

    def _build_mode_buttons(self, layout: QVBoxLayout) -> None:
        panel = QWidget()
        panel.setObjectName("sensor_mode_switch")
        row = QHBoxLayout(panel)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        for label, callback in [
            ("Overview", self.show_overview),
            ("All Sensors", self.show_raw_explorer),
            ("CPU Diagnostics", self.show_cpu_diagnostics),
            ("Favorites", self.show_favorites),
        ]:
            button = QPushButton(label)
            button.setObjectName("sensor_mode_button")
            button.clicked.connect(callback)
            row.addWidget(button)
        row.addStretch(1)
        layout.addWidget(panel)

    def _build_hardware_panels(self, layout: QVBoxLayout) -> None:
        self.hardware_section = QWidget()
        self.hardware_section.setObjectName("sensor_hardware_panels")
        section_layout = QVBoxLayout(self.hardware_section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(12)
        section_layout.addWidget(SectionHeader("Hardware Panels", "Dashboard-style summaries with compact detail rows instead of raw tables."))
        self.hardware_grid = QGridLayout()
        self.hardware_grid.setHorizontalSpacing(14)
        self.hardware_grid.setVerticalSpacing(14)
        section_layout.addLayout(self.hardware_grid)
        layout.addWidget(self.hardware_section)

    def _build_favorites_section(self, layout: QVBoxLayout) -> None:
        self.favorites_section = QWidget()
        self.favorites_section.setObjectName("sensor_favorites_section")
        section_layout = QVBoxLayout(self.favorites_section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(10)
        section_layout.addWidget(SectionHeader("Favorite Sensors", "Pinned sensors from app-side config/sensor_favorites.json."))
        self.favorite_grid = QGridLayout()
        self.favorite_grid.setHorizontalSpacing(10)
        self.favorite_grid.setVerticalSpacing(10)
        section_layout.addLayout(self.favorite_grid)
        layout.addWidget(self.favorites_section)

    def _build_raw_explorer(self, layout: QVBoxLayout) -> None:
        self.raw_section, raw_layout = make_card("All Sensors Explorer", "Every raw sensor remains visible here. Filters never delete or permanently hide readings.")
        self.raw_section.setObjectName("sensor_raw_explorer_section")

        self.raw_search = QLineEdit()
        self.raw_search.setObjectName("sensor_raw_search")
        self.raw_search.setPlaceholderText("Search source, hardware, type, name, category, key, or notes")
        self.raw_search.textChanged.connect(self.refresh_raw_table)
        raw_layout.addWidget(self.raw_search)

        filter_panel = QWidget()
        filter_panel.setObjectName("sensor_raw_filter_panel")
        filter_row = QHBoxLayout(filter_panel)
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)
        self.hardware_filter = QComboBox()
        self.hardware_filter.currentTextChanged.connect(self.refresh_raw_table)
        self.sensor_type_filter = QComboBox()
        self.sensor_type_filter.currentTextChanged.connect(self.refresh_raw_table)
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self.refresh_raw_table)
        self.selected_only = QCheckBox("Selected/headline")
        self.problem_only = QCheckBox("Problems only")
        self.favorite_only = QCheckBox("Favorites only")
        for box in (self.selected_only, self.problem_only, self.favorite_only):
            box.stateChanged.connect(self.refresh_raw_table)
        filter_row.addWidget(QLabel("Hardware"))
        filter_row.addWidget(self.hardware_filter)
        filter_row.addWidget(QLabel("Type"))
        filter_row.addWidget(self.sensor_type_filter)
        filter_row.addWidget(QLabel("Category"))
        filter_row.addWidget(self.category_filter)
        filter_row.addWidget(self.selected_only)
        filter_row.addWidget(self.problem_only)
        filter_row.addWidget(self.favorite_only)
        filter_row.addStretch(1)
        raw_layout.addWidget(filter_panel)

        action_panel = QWidget()
        action_row = QHBoxLayout(action_panel)
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(8)
        self.raw_count_label = QLabel("Showing 0 of 0 sensors")
        self.raw_count_label.setObjectName("sensor_raw_count_label")
        pin_button = QPushButton("Pin Selected Sensor")
        pin_button.clicked.connect(self.pin_selected_sensor)
        unpin_button = QPushButton("Unpin Selected Sensor")
        unpin_button.clicked.connect(self.unpin_selected_sensor)
        clear_button = QPushButton("Clear Filters")
        clear_button.clicked.connect(self.clear_raw_filters)
        export_button = QPushButton("Export Raw Snapshot")
        export_button.clicked.connect(self.export_raw_snapshot)
        action_row.addWidget(self.raw_count_label, 1)
        action_row.addWidget(pin_button)
        action_row.addWidget(unpin_button)
        action_row.addWidget(clear_button)
        action_row.addWidget(export_button)
        raw_layout.addWidget(action_panel)

        self.raw_table = QTableWidget()
        self.raw_table.setObjectName("sensor_all_raw_explorer_table")
        self.raw_table.setMinimumHeight(520)
        raw_layout.addWidget(self.raw_table)
        layout.addWidget(self.raw_section)

    def _build_cpu_diagnostics(self, layout: QVBoxLayout) -> None:
        self.cpu_diag_section = QWidget()
        self.cpu_diag_section.setObjectName("sensor_cpu_diagnostics_panel")
        diag_layout = QVBoxLayout(self.cpu_diag_section)
        diag_layout.setContentsMargins(0, 0, 0, 0)
        diag_layout.setSpacing(12)
        diag_layout.addWidget(SectionHeader("CPU Temperature Diagnostics", "Why the CPU headline was selected, or why it was rejected."))

        self.cpu_diag_summary_card, summary_layout = make_card("Diagnostic Summary")
        self.cpu_diag_summary = QLabel("CPU temperature diagnostics not read yet.")
        self.cpu_diag_summary.setObjectName("sensor_cpu_diagnostics_summary")
        self.cpu_diag_summary.setWordWrap(True)
        summary_layout.addWidget(self.cpu_diag_summary)
        self.cpu_warning = QLabel("")
        self.cpu_warning.setObjectName("diagnostics_warning_card")
        self.cpu_warning.setWordWrap(True)
        summary_layout.addWidget(self.cpu_warning)
        diag_layout.addWidget(self.cpu_diag_summary_card)

        self.cpu_accepted_card, accepted_layout = make_card("Accepted CPU Temperature Candidates", "Valid CPU-like temperature readings and ranking reasons.")
        self.cpu_accepted_card.setObjectName("sensor_cpu_accepted_candidates_panel")
        self.cpu_accepted_card.setMinimumHeight(200)
        self.cpu_accepted_table = QTableWidget()
        self.cpu_accepted_table.setObjectName("sensor_cpu_accepted_candidates_table")
        self.cpu_accepted_table.setMinimumHeight(170)
        accepted_layout.addWidget(self.cpu_accepted_table)
        diag_layout.addWidget(self.cpu_accepted_card)

        rejected_card, rejected_layout = make_card("Rejected Candidates", "Grouped rejection reasons make hidden or invalid readings obvious.")
        self.cpu_rejected_table = QTableWidget()
        self.cpu_rejected_table.setObjectName("sensor_cpu_rejected_candidates_table")
        self.cpu_rejected_table.setMinimumHeight(260)
        rejected_layout.addWidget(self.cpu_rejected_table)
        diag_layout.addWidget(rejected_card)

        raw_cpu_card, raw_cpu_layout = make_card("Raw CPU Sensors", "All CPU-category sensors, including load, power, clock, voltage, and temperature.")
        self.cpu_raw_table = QTableWidget()
        self.cpu_raw_table.setObjectName("sensor_cpu_raw_table")
        self.cpu_raw_table.setMinimumHeight(280)
        raw_cpu_layout.addWidget(self.cpu_raw_table)
        diag_layout.addWidget(raw_cpu_card)
        layout.addWidget(self.cpu_diag_section)

    def _presentmon_controls(self) -> QHBoxLayout:
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.presentmon_candidate = QComboBox()
        candidates = [row.get("path", "") for row in self.window.presentmon.candidates()]
        self.presentmon_candidate.addItems(candidates or [""])
        self.presentmon_candidate.setMinimumWidth(220)
        self.presentmon_candidate.setMaximumWidth(520)
        self.presentmon_process = QLineEdit()
        self.presentmon_process.setPlaceholderText("Optional process name, e.g. BF6.exe")
        self.presentmon_process.setMaximumWidth(180)
        self.presentmon_duration = QSpinBox()
        self.presentmon_duration.setRange(1, 600)
        self.presentmon_duration.setValue(60)
        self.presentmon_duration.setMaximumWidth(90)
        start_pm = QPushButton("Start PresentMon")
        start_pm.clicked.connect(self.start_presentmon)
        stop_pm = QPushButton("Stop PresentMon")
        stop_pm.clicked.connect(self.stop_presentmon)
        controls.addWidget(QLabel("Candidate"))
        controls.addWidget(self.presentmon_candidate, 2)
        controls.addWidget(QLabel("Process"))
        controls.addWidget(self.presentmon_process, 1)
        controls.addWidget(QLabel("Seconds"))
        controls.addWidget(self.presentmon_duration)
        controls.addWidget(start_pm)
        controls.addWidget(stop_pm)
        return controls

    def refresh_all(self) -> None:
        if self.refresh_busy:
            self.status_label.setText("Refresh already running...")
            return
        self.refresh_busy = True
        self.status_label.setText("Refreshing sensors...")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self) -> None:
        payload: dict[str, Any] = {"started_local": time.strftime("%Y-%m-%d %H:%M:%S")}
        try:
            payload["nvidia"] = self.window.nvidia.telemetry_snapshot()
        except Exception as exc:
            payload["nvidia"] = {"ok": False, "error": str(exc)}
        try:
            payload["presentmon"] = self.window.presentmon.latest_reading()
        except Exception as exc:
            payload["presentmon"] = {"ok": False, "error": str(exc)}
        try:
            payload["lhm"] = self.window.lhm.sensor_snapshot()
        except Exception as exc:
            payload["lhm"] = {"ok": False, "source": "librehardwaremonitor", "error": str(exc), "sensors": []}
        payload["finished_local"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.refresh_signals.ready.emit(payload)

    def _apply_refresh_payload(self, payload: dict[str, Any]) -> None:
        self.refresh_busy = False
        self.window.latest_nvidia_snapshot = payload.get("nvidia", {})
        self.window.latest_presentmon_snapshot = payload.get("presentmon", {})
        self.window.latest_lhm_snapshot = payload.get("lhm", {})
        model = self.window.collect_normalized_telemetry(
            lhm_snapshot=self.window.latest_lhm_snapshot,
            nvidia_snapshot=self.window.latest_nvidia_snapshot,
            presentmon_snapshot=self.window.latest_presentmon_snapshot,
            record_history=True,
        )
        self.current_model = model
        self._render_model(model)
        error_bits = [value.get("error") for value in payload.values() if isinstance(value, dict) and value.get("error")]
        suffix = f" | last error: {error_bits[0]}" if error_bits else ""
        self.status_label.setText(f"Last refresh: {payload.get('finished_local')} | raw sensors: {len(model.get('raw_sensors', []))}{suffix}")

    def _render_model(self, model: dict[str, Any]) -> None:
        self.current_raw_rows = model.get("raw_sensors", [])
        presenter = SensorPresentation(model, self.window.sensor_history, self.timer.isActive())
        self.current_presentation = presenter.build()
        self.current_raw_table_rows = self.current_presentation.get("raw_table_rows", [])
        self._render_status_pills(self.current_presentation.get("status_pills", []))
        self._render_hero_cards(self.current_presentation.get("hero_cards", []))
        self._render_hardware_panels(self.current_presentation.get("hardware_panels", []))
        self._render_favorites(self.current_presentation.get("favorite_cards", []))
        self._refresh_filter_options()
        self.refresh_raw_table()
        self._render_cpu_diagnostics(self.current_presentation.get("diagnostics", {}))

    def _render_status_pills(self, pills: list[dict[str, Any]]) -> None:
        while self.status_pills_layout.count():
            item = self.status_pills_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for pill in pills:
            self.status_pills_layout.addWidget(StatusPill(str(pill.get("label")), str(pill.get("value")), str(pill.get("tone") or "neutral")))
        self.status_pills_layout.addStretch(1)

    def _render_hero_cards(self, cards: list[dict[str, Any]]) -> None:
        while self.hero_layout.count():
            item = self.hero_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.hero_cards.clear()
        for index, card_data in enumerate(cards):
            card = HeroMetricCard(card_data)
            self.hero_cards[str(card_data.get("key") or index)] = card
            self.hero_layout.addWidget(card, 0, index)

    def _render_hardware_panels(self, panels: list[dict[str, Any]]) -> None:
        while self.hardware_grid.count():
            item = self.hardware_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.hardware_panels.clear()
        for index, panel_data in enumerate(panels):
            panel = HardwarePanel(panel_data)
            if panel_data.get("key") == "frames":
                panel.layout().addLayout(self._presentmon_controls())
            self.hardware_panels[str(panel_data.get("key") or index)] = panel
            self.hardware_grid.addWidget(panel, index // 2, index % 2)

    def _render_favorites(self, favorites: list[dict[str, Any]]) -> None:
        while self.favorite_grid.count():
            item = self.favorite_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not favorites:
            empty = QLabel("No favorites pinned yet. Select a row in All Sensors and use Pin Selected Sensor.")
            empty.setObjectName("sensor_empty_state")
            empty.setWordWrap(True)
            self.favorite_grid.addWidget(empty, 0, 0)
            return
        for index, favorite in enumerate(favorites[:12]):
            card, card_layout = make_card(str(favorite.get("title") or "Favorite"), str(favorite.get("subtitle") or ""))
            card.setObjectName("favorite_sensor_card")
            card_layout.addWidget(MetricChip("Value", str(favorite.get("value_display") or "unavailable")))
            card_layout.addWidget(MetricChip("Source", str(favorite.get("source") or "")))
            self.favorite_grid.addWidget(card, index // 4, index % 4)

    def _refresh_filter_options(self) -> None:
        selections = {
            "hardware": self.hardware_filter.currentText() if self.hardware_filter.count() else "All",
            "sensor_type": self.sensor_type_filter.currentText() if self.sensor_type_filter.count() else "All",
            "category": self.category_filter.currentText() if self.category_filter.count() else "All",
        }
        options = {
            "hardware": sorted({str(row.get("hardware_type") or row.get("hardware") or "Unknown") for row in self.current_raw_rows}),
            "sensor_type": sorted({str(row.get("sensor_type") or "Unknown") for row in self.current_raw_rows}),
            "category": sorted({str(row.get("category") or "other") for row in self.current_raw_rows}),
        }
        for combo, key in [(self.hardware_filter, "hardware"), (self.sensor_type_filter, "sensor_type"), (self.category_filter, "category")]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(["All"] + options[key])
            wanted = selections[key]
            if wanted in ["All"] + options[key]:
                combo.setCurrentText(wanted)
            combo.blockSignals(False)

    def refresh_raw_table(self) -> None:
        query = self.raw_search.text().strip().lower() if hasattr(self, "raw_search") else ""
        hardware = self.hardware_filter.currentText() if hasattr(self, "hardware_filter") and self.hardware_filter.count() else "All"
        sensor_type = self.sensor_type_filter.currentText() if hasattr(self, "sensor_type_filter") and self.sensor_type_filter.count() else "All"
        category = self.category_filter.currentText() if hasattr(self, "category_filter") and self.category_filter.count() else "All"
        rows = []
        for row in self.current_raw_table_rows:
            raw = row.get("raw", {})
            searchable = " ".join(str(row.get(key, "")) for key in ["source", "hardware", "hardware_type", "sensor_type", "name", "category", "key", "notes"]).lower()
            if query and query not in searchable:
                continue
            if hardware != "All" and hardware not in (str(raw.get("hardware_type")), str(raw.get("hardware"))):
                continue
            if sensor_type != "All" and sensor_type != str(raw.get("sensor_type")):
                continue
            if category != "All" and category != str(raw.get("category")):
                continue
            if self.selected_only.isChecked() and not row.get("selected"):
                continue
            if self.favorite_only.isChecked() and row.get("favorite") != "yes":
                continue
            if self.problem_only.isChecked() and raw.get("value") is not None and raw.get("confidence") != "unavailable" and "rejected" not in str(raw.get("notes", "")).lower():
                continue
            rows.append(row)
        self.filtered_raw_rows = rows
        self.raw_count_label.setText(f"Showing {len(rows)} of {len(self.current_raw_table_rows)} sensors")
        fill_table(
            self.raw_table,
            ["Favorite", "Selected", "Category", "Hardware", "Sensor type", "Name", "Value", "Unit", "Notes", "Source", "Hardware type", "Min", "Max", "Key", "Score"],
            [
                [
                    row.get("favorite"),
                    row.get("selected"),
                    row.get("category"),
                    row.get("hardware"),
                    row.get("sensor_type"),
                    row.get("name"),
                    row.get("value"),
                    row.get("unit"),
                    row.get("notes"),
                    row.get("source"),
                    row.get("hardware_type"),
                    row.get("min"),
                    row.get("max"),
                    row.get("key"),
                    row.get("score"),
                ]
                for row in rows
            ],
        )

    def _render_cpu_diagnostics(self, diagnostics: dict[str, Any]) -> None:
        cpu = diagnostics.get("cpu_temperature", {}) or {}
        selected = cpu.get("selected")
        self.cpu_diag_summary.setText(
            "\n".join(
                [
                    f"Selected CPU temp: {selected.get('name')} = {selected.get('value')} C" if selected else "Selected CPU temp: unavailable",
                    f"Total temperature sensors: {cpu.get('total_temperature_sensors', 0)}",
                    f"CPU hardware temperature sensors: {cpu.get('cpu_hardware_temperature_sensors', 0)}",
                    f"Summary: {cpu.get('summary') or 'none'}",
                ]
            )
        )
        warning = cpu.get("warning") or ""
        self.cpu_warning.setText(warning)
        self.cpu_warning.setVisible(bool(warning))
        fill_table(
            self.cpu_accepted_table,
            ["Name", "Hardware", "Value", "Score", "Reason"],
            [[row.get("name"), row.get("hardware"), row.get("value"), row.get("score"), row.get("reason")] for row in cpu.get("accepted_candidates", [])],
        )
        rejected_rows = []
        for reason, rows in (cpu.get("rejected_by_reason") or {}).items():
            for row in rows:
                rejected_rows.append([reason, row.get("name"), row.get("hardware"), row.get("value"), row.get("reason")])
        fill_table(self.cpu_rejected_table, ["Group", "Name", "Hardware", "Value", "Reason"], rejected_rows)
        fill_table(
            self.cpu_raw_table,
            ["Source", "Hardware", "Type", "Name", "Value", "Unit", "Selected", "Notes"],
            [
                [
                    row.get("source"),
                    row.get("hardware"),
                    row.get("sensor_type"),
                    row.get("name"),
                    row.get("display_value"),
                    row.get("unit"),
                    ", ".join(row.get("selected_for", [])) if row.get("selected_for") else "",
                    row.get("notes"),
                ]
                for row in cpu.get("raw_cpu_sensors", [])
            ],
        )

    def pin_selected_sensor(self) -> None:
        row = self._selected_raw_row()
        if row is None:
            QMessageBox.information(self, "No sensor selected", "Select a raw sensor row first.")
            return
        raw = row.get("raw", {})
        favorite = {
            "source": raw.get("source"),
            "hardware": raw.get("hardware"),
            "sensor_type": raw.get("sensor_type"),
            "name": raw.get("name"),
            "label": raw.get("display_name") or raw.get("name"),
        }
        favorites = self.window.sensor_favorites.setdefault("favorites", [])
        if favorite not in favorites:
            favorites.append(favorite)
        save_json_inside_phase7(self.window.paths.config_dir / "sensor_favorites.json", self.window.sensor_favorites, self.window.paths)
        self._render_model(self.window.collect_normalized_telemetry(record_history=False))

    def unpin_selected_sensor(self) -> None:
        row = self._selected_raw_row()
        if row is None:
            QMessageBox.information(self, "No sensor selected", "Select a raw sensor row first.")
            return
        raw = row.get("raw", {})
        before = len(self.window.sensor_favorites.get("favorites", []))
        self.window.sensor_favorites["favorites"] = [
            favorite
            for favorite in self.window.sensor_favorites.get("favorites", [])
            if not (
                favorite.get("source") == raw.get("source")
                and favorite.get("hardware") == raw.get("hardware")
                and favorite.get("sensor_type") == raw.get("sensor_type")
                and favorite.get("name") == raw.get("name")
            )
        ]
        if len(self.window.sensor_favorites.get("favorites", [])) != before:
            save_json_inside_phase7(self.window.paths.config_dir / "sensor_favorites.json", self.window.sensor_favorites, self.window.paths)
        self._render_model(self.window.collect_normalized_telemetry(record_history=False))

    def _selected_raw_row(self) -> dict[str, Any] | None:
        selected = self.raw_table.currentRow()
        if selected < 0 or selected >= len(self.filtered_raw_rows):
            return None
        return self.filtered_raw_rows[selected]

    def clear_raw_filters(self) -> None:
        self.raw_search.clear()
        for combo in (self.hardware_filter, self.sensor_type_filter, self.category_filter):
            combo.setCurrentText("All")
        for box in (self.selected_only, self.problem_only, self.favorite_only):
            box.setChecked(False)
        self.refresh_raw_table()

    def export_raw_snapshot(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = self.window.paths.raw_outputs_dir / f"sensor_raw_snapshot_phase7_{timestamp}.json"
        data = {
            "generated_local": datetime.now().isoformat(timespec="seconds"),
            "count": len(self.current_raw_rows),
            "sensors": self.current_raw_rows,
        }
        save_json_inside_phase7(path, data, self.window.paths)
        QMessageBox.information(self, "Raw sensor snapshot exported", f"Saved app-side snapshot only:\n{path}")

    def toggle_polling(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Resume Live Polling")
        else:
            self.timer.start()
            self.pause_button.setText("Pause Live Polling")
        self._render_model(self.current_model)

    def start_presentmon(self) -> None:
        process_name = self.presentmon_process.text().strip() or None
        candidate = self.presentmon_candidate.currentText() or None
        result = self.window.presentmon.start_capture(process_name=process_name, duration_seconds=int(self.presentmon_duration.value()), candidate_path=candidate)
        if not result.get("ok"):
            QMessageBox.warning(self, "PresentMon start failed", str(result.get("error")))
        self.refresh_all()

    def stop_presentmon(self) -> None:
        self.window.presentmon.stop_capture()
        self.refresh_all()

    def save_polling(self) -> None:
        polling = self.surface.app_config.setdefault("polling", {})
        polling["enabled"] = self.timer.isActive()
        polling["interval_seconds"] = int(self.timer.interval() / 1000)
        path = self.surface.save_app_config()
        QMessageBox.information(self, "Polling settings saved", f"Saved app-side config only:\n{path}")

    def show_overview(self) -> None:
        self._scroll_to(self.hero_strip)

    def show_hardware_panels(self) -> None:
        self._scroll_to(self.hardware_section)

    def show_raw_explorer(self) -> None:
        self._scroll_to(self.raw_section)

    def show_cpu_diagnostics(self) -> None:
        self._scroll_to(self.cpu_diag_section)

    def show_favorites(self) -> None:
        self._scroll_to(self.favorites_section)

    def _scroll_to(self, widget: QWidget) -> None:
        if self.scroll_area is None:
            return
        self.scroll_area.verticalScrollBar().setValue(max(0, widget.y() - 12))
