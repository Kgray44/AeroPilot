from __future__ import annotations

from typing import Any


class GigabyteAdapter:
    def __init__(self, phase1_gigabyte: dict[str, Any]) -> None:
        self.phase1 = phase1_gigabyte

    def status(self) -> dict[str, Any]:
        return {
            "installed_entries": self.phase1.get("installed_entries", []),
            "running_processes": self.phase1.get("running_processes", []),
            "services": self.phase1.get("services", []),
            "folders": self.phase1.get("folders", []),
            "obvious_config_files": self.phase1.get("obvious_config_files", []),
            "fan_control_feasibility": self.phase1.get("fan_control_feasibility", []),
            "phase2_control_enabled": False,
        }
