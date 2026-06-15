from __future__ import annotations

import threading
import time
from typing import Any

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.config_loader import save_json_inside_phase6
from app.ui.common import add_form_row, fill_table, make_card, make_page_header, make_scroll_page
from app.ui.telemetry_widgets import MetricCard, MiniHistoryChart


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
        self.current_raw_rows: list[dict[str, Any]] = []
        self.filtered_raw_rows: list[dict[str, Any]] = []

        self.timer = QTimer(self)
        interval = int(self.surface.app_config.get("polling", {}).get("interval_seconds", 5))
        self.timer.setInterval(max(3, interval) * 1000)
        self.timer.timeout.connect(self.refresh_all)

        layout, _body = make_scroll_page(self)
        layout.addWidget(
            make_page_header(
                "Sensors / Telemetry",
                "A read-only telemetry command center for NVIDIA, LibreHardwareMonitor, and opt-in PresentMon capture.",
                [("Telemetry only", "safe"), ("PresentMon manual start", "neutral"), ("All writes blocked", "warn")],
            )
        )

        self.status_label = QLabel("Last refresh: not read yet")
        self.status_label.setObjectName("sensor_refresh_status")
        controls = QHBoxLayout()
        refresh = QPushButton("Refresh All")
        refresh.setObjectName("sensor_refresh_button")
        refresh.clicked.connect(self.refresh_all)
        self.pause_button = QPushButton("Pause Live Polling")
        self.pause_button.setObjectName("sensor_pause_resume_button")
        self.pause_button.clicked.connect(self.toggle_polling)
        controls.addWidget(refresh)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.status_label, 1)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.overview_grid = QGridLayout()
        self.overview_grid.setHorizontalSpacing(12)
        self.overview_grid.setVerticalSpacing(12)
        overview_panel = QWidget()
        overview_panel.setObjectName("sensor_overview_cards")
        overview_panel.setLayout(self.overview_grid)
        layout.addWidget(overview_panel)
        self.metric_cards: dict[str, MetricCard] = {}

        charts_card, charts_layout = make_card("Live trends", "Small in-memory traces for the newest samples. Nothing is logged to disk unless app-side telemetry logging is enabled.")
        charts_card.setObjectName("sensor_history_panel")
        chart_grid = QGridLayout()
        self.history_charts: dict[str, MiniHistoryChart] = {}
        for index, (key, title) in enumerate(
            [
                ("cpu_temp_c", "CPU temp"),
                ("cpu_load_percent", "CPU load"),
                ("gpu_temp_c", "GPU temp"),
                ("gpu_util_percent", "GPU load"),
                ("fps", "FPS"),
                ("fan_rpm", "Fan RPM"),
            ]
        ):
            panel, panel_layout = make_card(title)
            chart = MiniHistoryChart()
            self.history_charts[key] = chart
            panel_layout.addWidget(chart)
            chart_grid.addWidget(panel, index // 3, index % 3)
        charts_layout.addLayout(chart_grid)
        layout.addWidget(charts_card)

        self.view_tabs = QTabWidget()
        self.view_tabs.setObjectName("sensor_view_tabs")
        self.view_tabs.addTab(self._build_grouped_view(), "Grouped Panels")
        self.view_tabs.addTab(self._build_raw_view(), "All Sensors")
        self.view_tabs.addTab(self._build_cpu_diagnostics_view(), "CPU Diagnostics")
        layout.addWidget(self.view_tabs)

        if self.surface.app_config.get("polling", {}).get("enabled", False):
            self.timer.start()
        self._render_model(self.current_model)
        self.refresh_all()

    def _build_grouped_view(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.favorite_card, self.favorite_layout = make_card("Favorite sensors", "Pinned sensors are saved in config/sensor_favorites.json inside the Phase 6 folder.")
        self.favorite_panel = QWidget()
        self.favorite_panel.setObjectName("sensor_favorites_panel")
        self.favorite_grid = QGridLayout(self.favorite_panel)
        self.favorite_layout.addWidget(self.favorite_panel)
        layout.addWidget(self.favorite_card)

        self.group_tables: dict[str, QTableWidget] = {}
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        groups = [
            ("cpu", "CPU panel", "Best temp, candidates, load, power, clock, voltage, and core/thread readings."),
            ("gpu", "GPU panel", "nvidia-smi and LHM GPU readings, including temperatures, utilization, power, clocks, and VRAM."),
            ("memory", "Memory panel", "RAM usage/load and memory-controller readings when exposed."),
            ("fans", "Fans / Cooling panel", "Fan RPM sensors when the laptop firmware exposes them."),
            ("storage", "Storage panel", "SSD/HDD temperatures and storage activity/load sensors."),
            ("network", "Network / Other panel", "Network, battery/AC, motherboard, controller, and uncategorized sensors."),
            ("frames", "PresentMon panel", "Manual frame capture state, latest FPS, frame time, process, runtime, and output file."),
        ]
        for index, (key, title, subtitle) in enumerate(groups):
            card, card_layout = make_card(title, subtitle)
            table = QTableWidget()
            table.setMinimumHeight(170)
            table.setObjectName(f"sensor_group_table_{key}")
            self.group_tables[key] = table
            card_layout.addWidget(table)
            if key == "frames":
                card_layout.addLayout(self._presentmon_controls())
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        return page

    def _presentmon_controls(self) -> QHBoxLayout:
        controls = QHBoxLayout()
        self.presentmon_candidate = QComboBox()
        candidates = [row.get("path", "") for row in self.window.presentmon.candidates()]
        self.presentmon_candidate.addItems(candidates or [""])
        self.presentmon_process = QLineEdit()
        self.presentmon_process.setPlaceholderText("Optional process name, e.g. BF6.exe")
        self.presentmon_duration = QSpinBox()
        self.presentmon_duration.setRange(1, 600)
        self.presentmon_duration.setValue(60)
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
        controls.addStretch(1)
        return controls

    def _build_raw_view(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        filter_row = QHBoxLayout()
        self.raw_search = QLineEdit()
        self.raw_search.setPlaceholderText("Search every raw sensor")
        self.raw_search.textChanged.connect(self.refresh_raw_table)
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
        pin_button = QPushButton("Pin Selected Sensor")
        pin_button.clicked.connect(self.pin_selected_sensor)
        filter_row.addWidget(self.raw_search, 2)
        filter_row.addWidget(QLabel("Hardware"))
        filter_row.addWidget(self.hardware_filter)
        filter_row.addWidget(QLabel("Type"))
        filter_row.addWidget(self.sensor_type_filter)
        filter_row.addWidget(QLabel("Category"))
        filter_row.addWidget(self.category_filter)
        filter_row.addWidget(self.selected_only)
        filter_row.addWidget(self.problem_only)
        filter_row.addWidget(self.favorite_only)
        filter_row.addWidget(pin_button)
        layout.addLayout(filter_row)
        self.raw_table = QTableWidget()
        self.raw_table.setObjectName("sensor_raw_explorer_table")
        self.raw_table.setMinimumHeight(520)
        layout.addWidget(self.raw_table)
        return page

    def _build_cpu_diagnostics_view(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.cpu_diag_summary = QLabel("CPU temperature diagnostics not read yet.")
        self.cpu_diag_summary.setWordWrap(True)
        self.cpu_diag_summary.setObjectName("sensor_cpu_diagnostics_summary")
        layout.addWidget(self.cpu_diag_summary)
        accepted_card, accepted_layout = make_card("Accepted CPU temperature candidates", "Valid CPU-like temperature sensors and why they were considered.")
        accepted_card.setMaximumHeight(260)
        self.cpu_accepted_table = QTableWidget()
        self.cpu_accepted_table.setObjectName("sensor_cpu_diagnostics_table")
        self.cpu_accepted_table.setFixedHeight(92)
        accepted_layout.addWidget(self.cpu_accepted_table)
        layout.addWidget(accepted_card)
        rejected_card, rejected_layout = make_card("Rejected temperature candidates", "Rejected sensors remain visible for debugging.")
        self.cpu_rejected_table = QTableWidget()
        self.cpu_rejected_table.setMinimumHeight(300)
        rejected_layout.addWidget(self.cpu_rejected_table)
        layout.addWidget(rejected_card)
        return page

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
        error_bits = [value.get("error") for key, value in payload.items() if isinstance(value, dict) and value.get("error")]
        suffix = f" | last error: {error_bits[0]}" if error_bits else ""
        self.status_label.setText(f"Last refresh: {payload.get('finished_local')} | raw sensors: {len(model.get('raw_sensors', []))}{suffix}")

    def _render_model(self, model: dict[str, Any]) -> None:
        self.current_raw_rows = model.get("raw_sensors", [])
        self._render_metric_cards(model.get("cards", []))
        self._render_history()
        self._render_groups(model)
        self._refresh_filter_options()
        self.refresh_raw_table()
        self._render_cpu_diagnostics(model)
        self._render_favorites(model)

    def _render_metric_cards(self, cards: list[dict[str, Any]]) -> None:
        while self.overview_grid.count():
            item = self.overview_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.metric_cards.clear()
        for index, card_data in enumerate(cards):
            widget = MetricCard(
                card_data.get("title", ""),
                str(card_data.get("value_display", "unavailable")),
                str(card_data.get("unit") or ""),
                str(card_data.get("subtitle") or ""),
                str(card_data.get("tone") or "normal"),
                card_data.get("progress"),
            )
            self.metric_cards[card_data.get("key", f"card_{index}")] = widget
            self.overview_grid.addWidget(widget, index // 5, index % 5)

    def _render_history(self) -> None:
        for key, chart in self.history_charts.items():
            chart.set_values(self.window.sensor_history.values(key), "normal")

    def _render_groups(self, model: dict[str, Any]) -> None:
        groups = model.get("groups", {})
        for key, table in self.group_tables.items():
            rows = groups.get(key, [])
            if key == "network":
                rows = groups.get("network", []) + groups.get("battery_power", []) + groups.get("motherboard", []) + groups.get("other", [])
            fill_table(
                table,
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
                    for row in rows[:80]
                ],
            )

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
        for row in self.current_raw_rows:
            searchable = " ".join(str(row.get(key, "")) for key in ["source", "hardware", "hardware_type", "sensor_type", "name", "category", "normalized_key", "notes"]).lower()
            if query and query not in searchable:
                continue
            if hardware != "All" and hardware not in (str(row.get("hardware_type")), str(row.get("hardware"))):
                continue
            if sensor_type != "All" and sensor_type != str(row.get("sensor_type")):
                continue
            if category != "All" and category != str(row.get("category")):
                continue
            if self.selected_only.isChecked() and not row.get("selected_for_headline") and not row.get("selected_for"):
                continue
            if self.favorite_only.isChecked() and not row.get("favorite"):
                continue
            if self.problem_only.isChecked() and row.get("value") is not None and row.get("confidence") != "unavailable":
                continue
            rows.append(row)
        self.filtered_raw_rows = rows
        fill_table(
            self.raw_table,
            ["Source", "Hardware", "Hardware type", "Sensor type", "Name", "Value", "Unit", "Min", "Max", "Category", "Key", "Selected", "Score", "Notes", "Favorite"],
            [
                [
                    row.get("source"),
                    row.get("hardware"),
                    row.get("hardware_type"),
                    row.get("sensor_type"),
                    row.get("name"),
                    row.get("display_value"),
                    row.get("unit"),
                    row.get("min"),
                    row.get("max"),
                    row.get("category"),
                    row.get("normalized_key"),
                    row.get("selected_for_headline") or ",".join(row.get("selected_for", [])),
                    row.get("score"),
                    row.get("notes"),
                    row.get("favorite"),
                ]
                for row in rows
            ],
        )

    def _render_cpu_diagnostics(self, model: dict[str, Any]) -> None:
        diag = model.get("diagnostics", {}).get("cpu_temperature", {})
        selected = diag.get("selected")
        self.cpu_diag_summary.setText(
            "\n".join(
                [
                    f"Selected CPU temp: {selected.get('name')} = {selected.get('value')} C" if selected else "Selected CPU temp: unavailable",
                    f"Total temperature sensors: {diag.get('total_temperature_sensors', 0)}",
                    f"CPU hardware temperature sensors: {diag.get('cpu_hardware_temperature_sensors', 0)}",
                    f"Failure reason: {diag.get('failure_reason') or 'none'}",
                ]
            )
        )
        fill_table(
            self.cpu_accepted_table,
            ["Name", "Hardware", "Value", "Score", "Reason"],
            [[row.get("name"), row.get("hardware"), row.get("value"), row.get("score"), row.get("reason")] for row in diag.get("accepted_candidates", [])],
        )
        fill_table(
            self.cpu_rejected_table,
            ["Name", "Hardware", "Value", "Reason"],
            [[row.get("name"), row.get("hardware"), row.get("value"), row.get("reason")] for row in diag.get("rejected_candidates", [])],
        )

    def _render_favorites(self, model: dict[str, Any]) -> None:
        while self.favorite_grid.count():
            item = self.favorite_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        favorites = [row for row in model.get("raw_sensors", []) if row.get("favorite")]
        if not favorites:
            label = QLabel("No favorites pinned yet. Use All Sensors -> Pin Selected Sensor.")
            label.setObjectName("card_subtitle")
            self.favorite_grid.addWidget(label, 0, 0)
            return
        for index, row in enumerate(favorites[:8]):
            card = MetricCard(str(row.get("name")), str(row.get("display_value")), str(row.get("unit") or ""), str(row.get("hardware")), "normal")
            self.favorite_grid.addWidget(card, index // 4, index % 4)

    def pin_selected_sensor(self) -> None:
        selected = self.raw_table.currentRow()
        if selected < 0 or selected >= len(self.filtered_raw_rows):
            QMessageBox.information(self, "No sensor selected", "Select a raw sensor row first.")
            return
        row = self.filtered_raw_rows[selected]
        favorite = {
            "source": row.get("source"),
            "hardware": row.get("hardware"),
            "sensor_type": row.get("sensor_type"),
            "name": row.get("name"),
            "label": row.get("display_name") or row.get("name"),
        }
        favorites = self.window.sensor_favorites.setdefault("favorites", [])
        if favorite not in favorites:
            favorites.append(favorite)
        save_json_inside_phase6(self.window.paths.config_dir / "sensor_favorites.json", self.window.sensor_favorites, self.window.paths)
        model = self.window.collect_normalized_telemetry(record_history=False)
        self._render_model(model)

    def toggle_polling(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Resume Live Polling")
        else:
            self.timer.start()
            self.pause_button.setText("Pause Live Polling")

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
        self.view_tabs.setCurrentIndex(0)

    def show_raw_explorer(self) -> None:
        self.view_tabs.setCurrentIndex(1)

    def show_cpu_diagnostics(self) -> None:
        self.view_tabs.setCurrentIndex(2)
