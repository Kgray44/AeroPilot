from __future__ import annotations

from typing import Any, Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


def make_badge(text: str, kind: str = "neutral") -> QLabel:
    label = QLabel(text)
    label.setObjectName(f"badge_{kind}")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label


def fill_table(table: QTableWidget, headers: list[str], rows: Iterable[Iterable[Any]]) -> None:
    data = [list(row) for row in rows]
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setRowCount(len(data))
    for row_index, row in enumerate(data):
        for column_index, value in enumerate(row):
            item = QTableWidgetItem("" if value is None else str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_index, column_index, item)
    table.resizeColumnsToContents()


def simple_panel(title: str, lines: list[str]) -> QWidget:
    panel = QWidget()
    layout = QVBoxLayout(panel)
    heading = QLabel(title)
    heading.setObjectName("panel_heading")
    layout.addWidget(heading)
    for line in lines:
        layout.addWidget(QLabel(line))
    layout.addStretch(1)
    return panel
