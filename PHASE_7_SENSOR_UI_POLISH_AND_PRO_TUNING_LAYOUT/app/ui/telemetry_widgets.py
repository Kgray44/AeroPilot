from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class MetricCard(QWidget):
    def __init__(self, title: str, value: str = "unavailable", unit: str = "", subtitle: str = "", tone: str = "normal", progress: float | None = None) -> None:
        super().__init__()
        self.setObjectName("telemetry_metric_card")
        self.setProperty("tone", tone)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("telemetry_metric_title")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("telemetry_metric_value")
        self.unit_label = QLabel(unit)
        self.unit_label.setObjectName("telemetry_metric_unit")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("telemetry_metric_subtitle")
        self.subtitle_label.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setObjectName("telemetry_metric_progress")
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        if unit:
            layout.addWidget(self.unit_label)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.progress)
        self.update_metric(title, value, unit, subtitle, tone, progress)

    def update_metric(self, title: str, value: str, unit: str = "", subtitle: str = "", tone: str = "normal", progress: float | None = None) -> None:
        self.title_label.setText(title)
        self.value_label.setText(value)
        self.unit_label.setText(unit)
        self.unit_label.setVisible(bool(unit))
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))
        self.setProperty("tone", tone)
        self.style().unpolish(self)
        self.style().polish(self)
        if progress is None:
            self.progress.hide()
        else:
            self.progress.show()
            self.progress.setValue(max(0, min(100, int(progress))))


class SensorBarCard(MetricCard):
    def __init__(self, title: str, value: str, unit: str = "", subtitle: str = "", tone: str = "normal", progress: float | None = None) -> None:
        super().__init__(title, value, unit, subtitle, tone, progress)
        self.setObjectName("telemetry_bar_card")


class MiniHistoryChart(QFrame):
    def __init__(self, values: Iterable[float] | None = None, tone: str = "normal") -> None:
        super().__init__()
        self.setObjectName("mini_history_chart")
        self.setMinimumHeight(62)
        self.values = list(values or [])
        self.tone = tone

    def set_values(self, values: Iterable[float], tone: str = "normal") -> None:
        self.values = list(values)
        self.tone = tone
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        painter.setPen(QPen(QColor("#d9e3ef"), 1))
        painter.drawRoundedRect(rect, 6, 6)
        values = [value for value in self.values if value is not None]
        if len(values) < 2:
            painter.setPen(QPen(QColor("#9aa8b8"), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "waiting for samples")
            return
        low = min(values)
        high = max(values)
        span = high - low if high != low else 1.0
        step = rect.width() / max(1, len(values) - 1)
        points = []
        for index, value in enumerate(values):
            x = rect.left() + index * step
            y = rect.bottom() - ((value - low) / span) * rect.height()
            points.append((x, y))
        color = {"safe": "#2c8a4b", "warn": "#c18410", "danger": "#bd2d2d", "unavailable": "#8794a3"}.get(self.tone, "#2867b2")
        painter.setPen(QPen(QColor(color), 2))
        for left, right in zip(points, points[1:]):
            painter.drawLine(int(left[0]), int(left[1]), int(right[0]), int(right[1]))


class MetricChip(QFrame):
    def __init__(self, label: str = "", value: str = "") -> None:
        super().__init__()
        self.setObjectName("metric_chip")
        self.setMaximumWidth(190)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)
        self.label_widget = QLabel(label)
        self.label_widget.setObjectName("metric_chip_label")
        self.value_widget = QLabel(value)
        self.value_widget.setObjectName("metric_chip_value")
        layout.addWidget(self.label_widget)
        layout.addWidget(self.value_widget)

    def update_chip(self, label: str, value: str) -> None:
        self.label_widget.setText(label)
        self.value_widget.setText(value)


class StatusPill(QFrame):
    def __init__(self, label: str = "", value: str = "", tone: str = "neutral") -> None:
        super().__init__()
        self.setObjectName("status_pill")
        self.setProperty("tone", tone)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        self.label_widget = QLabel(label)
        self.label_widget.setObjectName("status_pill_label")
        self.value_widget = QLabel(value)
        self.value_widget.setObjectName("status_pill_value")
        layout.addWidget(self.label_widget)
        layout.addWidget(self.value_widget)

    def update_pill(self, label: str, value: str, tone: str = "neutral") -> None:
        self.label_widget.setText(label)
        self.value_widget.setText(value)
        self.setProperty("tone", tone)
        self.style().unpolish(self)
        self.style().polish(self)


class SectionHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "") -> None:
        super().__init__()
        self.setObjectName("section_header")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("sensor_section_title")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("sensor_section_subtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        self.subtitle_label.setVisible(bool(subtitle))

    def update_header(self, title: str, subtitle: str = "") -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))


class HeroMetricCard(QFrame):
    def __init__(self, data: dict | None = None) -> None:
        super().__init__()
        self.setObjectName("hero_metric_card")
        self.setProperty("tone", "normal")
        self.setMinimumHeight(218)
        self.setMinimumWidth(0)
        self.setMaximumWidth(430)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        top = QHBoxLayout()
        self.title_label = QLabel("")
        self.title_label.setObjectName("hero_metric_title")
        self.source_badge = QLabel("")
        self.source_badge.setObjectName("source_badge")
        top.addWidget(self.title_label)
        top.addStretch(1)
        top.addWidget(self.source_badge)
        layout.addLayout(top)

        value_row = QHBoxLayout()
        value_row.setSpacing(6)
        self.value_label = QLabel("")
        self.value_label.setObjectName("hero_metric_value")
        self.value_label.setMinimumWidth(108)
        self.value_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.unit_label = QLabel("")
        self.unit_label.setObjectName("hero_metric_unit")
        value_row.addWidget(self.value_label)
        value_row.addWidget(self.unit_label)
        value_row.addStretch(1)
        layout.addLayout(value_row)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("hero_metric_subtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        self.progress = QProgressBar()
        self.progress.setObjectName("hero_metric_progress")
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        self.chart = MiniHistoryChart()
        self.chart.setObjectName("hero_mini_history_chart")
        self.chart.setMinimumHeight(48)
        layout.addWidget(self.chart)

        self.chip_panel = QWidget()
        self.chip_panel.setObjectName("hero_metric_chips")
        self.chip_layout = QGridLayout(self.chip_panel)
        self.chip_layout.setContentsMargins(0, 0, 0, 0)
        self.chip_layout.setHorizontalSpacing(7)
        self.chip_layout.setVerticalSpacing(6)
        layout.addWidget(self.chip_panel)

        self.update_card(data or {})

    def update_card(self, data: dict) -> None:
        tone = str(data.get("tone") or "normal")
        self.setProperty("tone", tone)
        self.title_label.setText(str(data.get("title") or "Metric"))
        self.value_label.setText(str(data.get("value_display") or "unavailable"))
        self.unit_label.setText(str(data.get("unit") or ""))
        self.unit_label.setVisible(bool(data.get("unit")))
        subtitle = str(data.get("subtitle") or "")
        if subtitle.strip().lower() == self.value_label.text().strip().lower():
            subtitle = ""
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))
        self.source_badge.setText(str(data.get("source") or "source"))
        progress = data.get("progress")
        if progress is None:
            self.progress.hide()
        else:
            self.progress.show()
            self.progress.setValue(max(0, min(100, int(float(progress)))))
        self.chart.set_values(data.get("history_values") or [], tone)
        self._render_chips(data.get("chips") or [])
        self.style().unpolish(self)
        self.style().polish(self)

    def _render_chips(self, chips: list[dict]) -> None:
        while self.chip_layout.count():
            item = self.chip_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for index, chip in enumerate(chips[:4]):
            self.chip_layout.addWidget(MetricChip(str(chip.get("label") or ""), str(chip.get("value") or "")), index // 2, index % 2)


class HardwarePanel(QFrame):
    def __init__(self, data: dict | None = None) -> None:
        super().__init__()
        self.setObjectName("hardware_panel")
        self.setProperty("tone", "normal")
        self.setMinimumHeight(260)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(11)
        self.title_label = QLabel("")
        self.title_label.setObjectName("hardware_panel_title")
        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("hardware_panel_subtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)

        self.metric_panel = QWidget()
        self.metric_panel.setObjectName("hardware_panel_metrics")
        self.metric_layout = QGridLayout(self.metric_panel)
        self.metric_layout.setContentsMargins(0, 0, 0, 0)
        self.metric_layout.setHorizontalSpacing(7)
        self.metric_layout.setVerticalSpacing(6)
        layout.addWidget(self.metric_panel)

        self.chart = MiniHistoryChart()
        self.chart.setObjectName("hardware_panel_chart")
        self.chart.setMinimumHeight(50)
        layout.addWidget(self.chart)

        self.details_title = QLabel("")
        self.details_title.setObjectName("hardware_panel_details_title")
        layout.addWidget(self.details_title)
        self.details_grid = QGridLayout()
        self.details_grid.setHorizontalSpacing(10)
        self.details_grid.setVerticalSpacing(6)
        layout.addLayout(self.details_grid)
        layout.addStretch(1)
        self.update_panel(data or {})

    def update_panel(self, data: dict) -> None:
        tone = str(data.get("tone") or "normal")
        self.setProperty("tone", tone)
        self.title_label.setText(str(data.get("title") or "Hardware"))
        self.subtitle_label.setText(str(data.get("subtitle") or ""))
        self.subtitle_label.setVisible(bool(data.get("subtitle")))
        self._render_chips(data.get("metrics") or [])
        self.chart.set_values(data.get("history_values") or [], tone)
        self.details_title.setText(str(data.get("details_title") or "Details"))
        self._render_details(data.get("details") or [], str(data.get("empty_text") or "No sensors available."))
        self.style().unpolish(self)
        self.style().polish(self)

    def _render_chips(self, chips: list[dict]) -> None:
        while self.metric_layout.count():
            item = self.metric_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for index, chip in enumerate(chips[:6]):
            self.metric_layout.addWidget(MetricChip(str(chip.get("label") or ""), str(chip.get("value") or "")), index // 3, index % 3)

    def _render_details(self, rows: list[dict], empty_text: str) -> None:
        while self.details_grid.count():
            item = self.details_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not rows:
            label = QLabel(empty_text)
            label.setObjectName("hardware_panel_empty")
            label.setWordWrap(True)
            self.details_grid.addWidget(label, 0, 0, 1, 2)
            return
        for index, row in enumerate(rows[:8]):
            name = QLabel(str(row.get("name") or "Sensor"))
            name.setObjectName("hardware_detail_name")
            value = QLabel(str(row.get("value") or "unavailable"))
            value.setObjectName("hardware_detail_value")
            self.details_grid.addWidget(name, index, 0)
            self.details_grid.addWidget(value, index, 1)
