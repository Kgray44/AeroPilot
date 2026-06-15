from __future__ import annotations

import json
from typing import Any

from app.core.command_runner import SafeCommandRunner


class PowerCfgAdapter:
    def __init__(self, runner: SafeCommandRunner, phase1_powercfg: dict[str, Any]) -> None:
        self.runner = runner
        self.phase1 = phase1_powercfg

    def active_scheme(self) -> dict[str, Any]:
        result = self.runner.run(["powercfg.exe", "/getactivescheme"], timeout=10, read_only=True)
        parsed = {
            "source": "live" if result.exit_code == 0 else "phase1",
            "raw": result.stdout,
            "name": self.phase1.get("active_scheme_name"),
            "guid": self.phase1.get("active_scheme_guid"),
            "command": result.to_dict(),
        }
        if result.stdout and "(" in result.stdout:
            try:
                parsed["guid"] = result.stdout.split("GUID:")[1].split("(")[0].strip()
                parsed["name"] = result.stdout.split("(", 1)[1].split(")", 1)[0].strip()
            except Exception:
                pass
        return parsed

    def settings_from_phase1(self) -> list[dict[str, Any]]:
        return list(self.phase1.get("processor_settings", []))

    def latest_cpu_snapshot(self, paths) -> dict[str, Any]:
        snapshot_dir = paths.phase4_root / "backups" / "snapshots"
        if not snapshot_dir.exists():
            return {"cpu_settings": []}
        snapshots = sorted(snapshot_dir.glob("cpu_readable_values_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not snapshots:
            return {"cpu_settings": []}
        try:
            return json.loads(snapshots[0].read_text(encoding="utf-8-sig"))
        except Exception:
            return {"cpu_settings": []}

    def current_values_by_control(self, paths) -> dict[str, dict[str, Any]]:
        snapshot = self.latest_cpu_snapshot(paths)
        return {row.get("control_id"): row for row in snapshot.get("cpu_settings", []) if row.get("control_id")}

    def refresh_setting(self, subgroup_guid: str, setting_guid: str) -> dict[str, Any]:
        result = self.runner.run(
            ["powercfg.exe", "/query", "SCHEME_CURRENT", subgroup_guid, setting_guid],
            timeout=15,
            read_only=True,
        )
        return {"ok": result.exit_code == 0, "raw": result.stdout, "command": result.to_dict()}
