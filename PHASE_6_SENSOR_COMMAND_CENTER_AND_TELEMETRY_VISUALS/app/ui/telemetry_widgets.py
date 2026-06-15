from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget


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
