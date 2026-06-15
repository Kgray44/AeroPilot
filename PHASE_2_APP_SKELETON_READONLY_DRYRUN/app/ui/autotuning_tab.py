from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class AutoTuningTab(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Planned workflow. All controls are disabled in Phase 2."))
        for text in [
            "Choose CPU preset",
            "Choose GPU profile slot",
            "Choose benchmark/game target",
            "Start telemetry",
            "Capture FPS/frame-time",
            "Capture ping",
            "Score result",
            "Compare presets",
            "Recommend best preset",
        ]:
            button = QPushButton(text)
            button.setEnabled(False)
            layout.addWidget(button)
        layout.addStretch(1)
