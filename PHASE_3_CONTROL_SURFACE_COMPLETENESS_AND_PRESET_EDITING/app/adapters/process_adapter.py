from __future__ import annotations

import json
from typing import Any

from app.core.command_runner import SafeCommandRunner


class ProcessAdapter:
    def __init__(self, runner: SafeCommandRunner, seed: dict[str, Any]) -> None:
        self.runner = runner
        self.seed = seed

    def targets(self) -> list[dict[str, Any]]:
        return list(self.seed.get("targets", []))

    def running_processes(self) -> list[dict[str, Any]]:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "Get-Process | Select-Object ProcessName,Id,Path | ConvertTo-Json -Depth 3",
        ]
        result = self.runner.run(command, timeout=20, read_only=True)
        if result.exit_code != 0 or not result.stdout.strip():
            return []
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
        if isinstance(data, dict):
            return [data]
        return list(data)

    def match_targets(self) -> list[dict[str, Any]]:
        processes = self.running_processes()
        process_names = {str(p.get("ProcessName", "")).lower(): p for p in processes}
        rows = []
        for target in self.targets():
            configured = list(target.get("process_names", []))
            matches = []
            for name in configured:
                for proc_name, proc in process_names.items():
                    if proc_name == name.lower() or proc_name.startswith(name.lower()):
                        matches.append(proc)
            rows.append(
                {
                    "id": target.get("id"),
                    "friendly": target.get("friendly"),
                    "category": target.get("category"),
                    "process_names": configured,
                    "running_now": bool(matches),
                    "matched_processes": matches,
                    "automation_enabled": False,
                }
            )
        return rows
