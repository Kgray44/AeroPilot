from __future__ import annotations

from typing import Any


class LibreHardwareMonitorAdapter:
    def __init__(self, phase1_lhm: dict[str, Any]) -> None:
        self.phase1 = phase1_lhm

    def status(self) -> dict[str, Any]:
        return {
            "found": bool(self.phase1.get("found")),
            "primary_executable_path": self.phase1.get("primary_executable_path"),
            "primary_library_path": self.phase1.get("primary_library_path"),
            "library_paths": self.phase1.get("library_paths", []),
            "phase2_loaded_dll": False,
            "notes": "Phase 2 does not launch sensor tools or load random DLLs.",
        }
