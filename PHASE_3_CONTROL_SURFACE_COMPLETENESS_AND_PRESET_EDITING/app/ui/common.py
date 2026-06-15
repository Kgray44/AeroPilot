from __future__ import annotations

from typing import Any, Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


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


def fill_controls_table(table: QTableWidget, controls: list[dict[str, Any]]) -> None:
    headers = [
        "Control ID",
        "Name",
        "Current value",
        "Desired/edit",
        "Risk",
        "Status",
        "UI section",
        "Dry-run",
        "Backup",
        "Restore",
        "Notes/warning",
    ]
    rows = []
    for control in controls:
        rows.append(
            [
                control.get("control_id"),
                control.get("friendly_name"),
                control.get("current_value", {}).get("display"),
                "editable" if control.get("desired_value_editing", {}).get("editable_in_phase3") else "not editable",
                control.get("risk", {}).get("level"),
                control.get("status"),
                control.get("ui_section"),
                "yes" if control.get("coverage", {}).get("has_dryrun_preview") else "no",
                "yes" if control.get("future_apply", {}).get("requires_backup") else "no",
                control.get("restore", {}).get("strategy"),
                control.get("risk", {}).get("warning") or control.get("notes"),
            ]
        )
    fill_table(table, headers, rows)


def filter_bar(risks: list[str], statuses: list[str], tabs: list[str] | None = None) -> tuple[QWidget, QLineEdit, QComboBox, QComboBox, QComboBox | None]:
    panel = QWidget()
    layout = QHBoxLayout(panel)
    search = QLineEdit()
    search.setPlaceholderText("Search controls")
    risk_box = QComboBox()
    risk_box.addItems(["All"] + sorted(set(risks)))
    status_box = QComboBox()
    status_box.addItems(["All"] + sorted(set(statuses)))
    tab_box = None
    layout.addWidget(QLabel("Search"))
    layout.addWidget(search, 2)
    layout.addWidget(QLabel("Risk"))
    layout.addWidget(risk_box)
    layout.addWidget(QLabel("Status"))
    layout.addWidget(status_box)
    if tabs is not None:
        tab_box = QComboBox()
        tab_box.addItems(["All"] + sorted(set(tabs)))
        layout.addWidget(QLabel("Tab"))
        layout.addWidget(tab_box)
    return panel, search, risk_box, status_box, tab_box


def table_rows_as_dicts(table: QTableWidget) -> list[dict[str, str]]:
    headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
    rows: list[dict[str, str]] = []
    for row in range(table.rowCount()):
        item: dict[str, str] = {}
        for col, header in enumerate(headers):
            cell = table.item(row, col)
            item[header] = cell.text() if cell else ""
        rows.append(item)
    return rows


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
