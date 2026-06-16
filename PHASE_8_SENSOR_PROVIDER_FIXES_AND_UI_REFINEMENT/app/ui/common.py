from __future__ import annotations

from typing import Any, Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
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


def make_scroll_page(parent: QWidget) -> tuple[QVBoxLayout, QWidget]:
    outer = QVBoxLayout(parent)
    outer.setContentsMargins(0, 0, 0, 0)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    body = QWidget()
    body.setObjectName("page_body")
    layout = QVBoxLayout(body)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(18)
    scroll.setWidget(body)
    outer.addWidget(scroll)
    return layout, body


def make_page_header(title: str, subtitle: str, badges: list[tuple[str, str]] | None = None) -> QWidget:
    panel = QWidget()
    panel.setObjectName("page_header")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    title_label = QLabel(title)
    title_label.setObjectName("page_title")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("page_subtitle")
    subtitle_label.setWordWrap(True)
    layout.addWidget(title_label)
    layout.addWidget(subtitle_label)
    if badges:
        row = QHBoxLayout()
        row.setSpacing(8)
        for text, kind in badges:
            row.addWidget(make_badge(text, kind))
        row.addStretch(1)
        layout.addLayout(row)
    return panel


def make_card(title: str | None = None, subtitle: str | None = None) -> tuple[QWidget, QVBoxLayout]:
    card = QWidget()
    card.setObjectName("card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(12)
    if title:
        heading = QLabel(title)
        heading.setObjectName("card_title")
        layout.addWidget(heading)
    if subtitle:
        sub = QLabel(subtitle)
        sub.setObjectName("card_subtitle")
        sub.setWordWrap(True)
        layout.addWidget(sub)
    return card, layout


def make_metric(label: str, value: str, tone: str = "neutral") -> QWidget:
    card, layout = make_card()
    card.setObjectName(f"metric_{tone}")
    value_label = QLabel(value)
    value_label.setObjectName("metric_value")
    label_widget = QLabel(label)
    label_widget.setObjectName("metric_label")
    label_widget.setWordWrap(True)
    layout.addWidget(value_label)
    layout.addWidget(label_widget)
    return card


def add_form_row(layout: QVBoxLayout, label: str, widget: QWidget, help_text: str | None = None) -> None:
    row = QWidget()
    row.setObjectName("form_row")
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(12)
    text_column = QVBoxLayout()
    text_column.setContentsMargins(0, 0, 0, 0)
    title = QLabel(label)
    title.setObjectName("form_label")
    text_column.addWidget(title)
    if help_text:
        hint = QLabel(help_text)
        hint.setObjectName("form_help")
        hint.setWordWrap(True)
        text_column.addWidget(hint)
    row_layout.addLayout(text_column, 1)
    row_layout.addWidget(widget, 1)
    layout.addWidget(row)


def horizontal_cards(cards: list[QWidget]) -> QWidget:
    panel = QWidget()
    layout = QHBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)
    for card in cards:
        layout.addWidget(card)
    layout.addStretch(1)
    return panel


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
