from __future__ import annotations

import re
from typing import Any

from app.core.command_runner import SafeCommandRunner


class PowerPlanAdapter:
    def __init__(self, runner: SafeCommandRunner) -> None:
        self.runner = runner

    def active_scheme(self) -> dict[str, Any]:
        result = self.runner.run(["powercfg.exe", "/getactivescheme"], timeout=10, read_only=True)
        parsed = self._parse_active_line(result.stdout)
        parsed.update({"ok": result.exit_code == 0, "raw": result.stdout, "command": result.to_dict()})
        return parsed

    def list_schemes(self) -> list[dict[str, Any]]:
        result = self.runner.run(["powercfg.exe", "/list"], timeout=15, read_only=True)
        rows: list[dict[str, Any]] = []
        active_guid = (self.active_scheme().get("guid") or "").lower()
        for line in (result.stdout or "").splitlines():
            match = re.search(r"Power Scheme GUID:\s*([a-fA-F0-9-]+)\s*\((.*?)\)(\s*\*)?", line)
            if not match:
                continue
            guid = match.group(1)
            rows.append(
                {
                    "guid": guid,
                    "name": match.group(2).strip(),
                    "active": bool(match.group(3)) or guid.lower() == active_guid,
                    "raw": line.strip(),
                }
            )
        return rows

    def create_clone_preview(self, source_guid: str, new_name: str) -> dict[str, Any]:
        safe_name = (new_name or "AeroTune cloned plan").strip()
        return {
            "preview_only": True,
            "blocked_in_phase5": True,
            "risk": "Medium",
            "requires_backup": True,
            "commands": [
                f'powercfg /duplicatescheme {source_guid}',
                f'powercfg /changename <new_scheme_guid> "{safe_name}"',
            ],
            "explanation": "This would create a new power plan clone later. Phase 5 does not execute it from the app.",
        }

    def set_active_preview(self, target_guid: str) -> dict[str, Any]:
        return {
            "preview_only": True,
            "blocked_in_phase5": True,
            "risk": "Medium",
            "requires_backup": True,
            "commands": [f"powercfg /setactive {target_guid}"],
            "explanation": "This would change the active Windows power plan later. Phase 5 keeps this disabled unless backup/restore gates are proven.",
        }

    def _parse_active_line(self, text: str) -> dict[str, Any]:
        parsed = {"guid": None, "name": None}
        match = re.search(r"Power Scheme GUID:\s*([a-fA-F0-9-]+)\s*\((.*?)\)", text or "")
        if match:
            parsed["guid"] = match.group(1)
            parsed["name"] = match.group(2).strip()
        return parsed
