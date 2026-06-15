from __future__ import annotations

from typing import Any

from app.core.dryrun import DryRunPreview, msi_profile_preview


class MsiAfterburnerAdapter:
    def __init__(self, phase1_msi: dict[str, Any], profile_config: dict[str, Any] | None = None) -> None:
        self.phase1 = phase1_msi
        self.profile_config = profile_config or {}

    def status(self) -> dict[str, Any]:
        return {
            "installed": bool(self.phase1.get("installed")),
            "executable_path": self.executable_path(),
            "rtss_path": self._first_path(self.phase1.get("rtss_executable_paths")),
            "install_folder": self.phase1.get("install_folder"),
            "profiles_folder": (self.phase1.get("profiles_folder") or {}).get("path"),
            "profile_files": self.phase1.get("profile_files", []),
            "config_files": self.phase1.get("config_files", []),
            "appears_running_phase1": bool(self.phase1.get("appears_running")),
        }

    def executable_path(self) -> str | None:
        return self._first_path(self.phase1.get("executable_paths"))

    def slots(self) -> list[dict[str, Any]]:
        configured = self.profile_config.get("slots", {})
        items = []
        for slot in range(1, 6):
            slot_config = configured.get(str(slot), {})
            items.append(
                {
                    "slot": slot,
                    "friendly_name": slot_config.get("friendly_name", f"Slot {slot}: Unverified"),
                    "verified": bool(slot_config.get("verified", False)),
                    "risk": "Medium",
                    "warning": "Wrong slot may apply an unintended GPU curve.",
                }
            )
        return items

    def preview_profile_command(self, slot: int) -> DryRunPreview:
        return msi_profile_preview(self.executable_path(), slot)

    @staticmethod
    def _first_path(items: Any) -> str | None:
        if not items:
            return None
        first = items[0]
        if isinstance(first, dict):
            return first.get("path")
        return str(first)
