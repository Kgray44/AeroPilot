from __future__ import annotations

from pathlib import Path
from typing import Any

from .config_loader import load_json


RISK_LABELS = [
    "Safe",
    "Low",
    "Medium",
    "High",
    "Dangerous / Experimental",
    "Read-only",
    "Unknown",
]


class RiskModel:
    def __init__(self, risk_catalog_path: Path) -> None:
        self.path = risk_catalog_path
        self.data = load_json(risk_catalog_path, {"items": [], "risk_labels": RISK_LABELS})
        self.items = list(self.data.get("items", []))

    def get_risk_for_control(self, name: str) -> str:
        item = self._find(name)
        return item.get("risk_level", "Unknown") if item else "Unknown"

    def get_warning_text(self, name: str) -> str:
        item = self._find(name)
        if not item:
            return "No risk catalog entry found."
        return item.get("suggested_warning_label") or item.get("what_can_go_wrong") or ""

    def get_default_enabled_state(self, name: str) -> str:
        item = self._find(name)
        return item.get("suggested_default_enabled_state", "Disabled") if item else "Disabled"

    def filter_by_category(self, category: str) -> list[dict[str, Any]]:
        return [item for item in self.items if item.get("category") == category]

    def filter_by_risk_level(self, risk_level: str) -> list[dict[str, Any]]:
        return [item for item in self.items if item.get("risk_level") == risk_level]

    def _find(self, name: str) -> dict[str, Any] | None:
        lowered = name.lower()
        for item in self.items:
            if item.get("setting_control_name", "").lower() == lowered:
                return item
        return None
