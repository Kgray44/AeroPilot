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
            "Get-CimInstance Win32_Process | Select-Object ProcessName,ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Depth 3",
        ]
        result = self.runner.run(command, timeout=20, read_only=True)
        if result.exit_code != 0 or not result.stdout.strip():
            fallback = self.runner.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    "Get-Process | Select-Object ProcessName,Id,Path | ConvertTo-Json -Depth 3",
                ],
                timeout=20,
                read_only=True,
            )
            if fallback.exit_code != 0 or not fallback.stdout.strip():
                return []
            try:
                data = json.loads(fallback.stdout)
            except json.JSONDecodeError:
                return []
            rows = [data] if isinstance(data, dict) else list(data)
            return [
                {
                    "ProcessName": row.get("ProcessName"),
                    "ProcessId": row.get("Id"),
                    "ExecutablePath": row.get("Path"),
                    "CommandLine": None,
                    "CommandLineUnavailable": True,
                }
                for row in rows
            ]
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
        if isinstance(data, dict):
            return [data]
        return list(data)

    def match_targets(self) -> list[dict[str, Any]]:
        processes = self.running_processes()
        rows = []
        for target in self.targets():
            configured = list(target.get("process_names", []))
            filters = [str(item).lower() for item in target.get("command_line_contains", []) if str(item).strip()]
            matches = []
            for name in configured:
                for proc in processes:
                    if not self._name_matches(proc, name):
                        continue
                    if self._is_known_false_positive(target, proc):
                        continue
                    command_status = self._command_line_matches(proc, filters)
                    if filters and not command_status["matched"]:
                        continue
                    matched = dict(proc)
                    matched["CommandLineMatched"] = command_status["matched"]
                    matched["CommandLineUnavailable"] = command_status["unavailable"]
                    matches.append(matched)
            rows.append(
                {
                    "id": target.get("id"),
                    "friendly": target.get("friendly"),
                    "category": target.get("category"),
                    "process_names": configured,
                    "command_line_contains": filters,
                    "running_now": bool(matches),
                    "matched_processes": matches,
                    "command_line_matched": bool(matches) and all(bool(m.get("CommandLineMatched")) for m in matches if filters),
                    "command_line_unavailable": any(bool(m.get("CommandLineUnavailable")) for m in matches),
                    "false_positive_warning": self._target_warning(target, filters),
                    "automation_enabled": False,
                }
            )
        return rows

    def _name_matches(self, proc: dict[str, Any], configured: str) -> bool:
        expected = configured.lower().strip()
        if not expected:
            return False
        actual = str(proc.get("ProcessName") or "").lower().strip()
        actual_base = actual[:-4] if actual.endswith(".exe") else actual
        expected_base = expected[:-4] if expected.endswith(".exe") else expected
        return actual_base == expected_base or actual == expected

    def _command_line_matches(self, proc: dict[str, Any], filters: list[str]) -> dict[str, bool]:
        command_line = proc.get("CommandLine")
        unavailable = command_line in (None, "")
        if not filters:
            return {"matched": True, "unavailable": unavailable}
        if unavailable:
            return {"matched": False, "unavailable": True}
        haystack = str(command_line).lower()
        return {"matched": all(token in haystack for token in filters), "unavailable": False}

    def _is_known_false_positive(self, target: dict[str, Any], proc: dict[str, Any]) -> bool:
        name = str(proc.get("ProcessName") or "").lower()
        cmd = str(proc.get("CommandLine") or "").lower()
        if target.get("id") == "steam" and "webhelper" in name:
            return True
        if "steamwebhelper" in name or "steamwebhelper" in cmd:
            return True
        return False

    def _target_warning(self, target: dict[str, Any], filters: list[str]) -> str:
        names = [str(name).lower() for name in target.get("process_names", [])]
        if any(name in ("java", "java.exe", "javaw", "javaw.exe") for name in names) and not filters:
            return "Broad Java process; command-line filtering required to avoid false positives."
        if target.get("id") == "steam":
            return "Launcher detection only; Steam webhelper is excluded and this is not treated as a game."
        return ""
