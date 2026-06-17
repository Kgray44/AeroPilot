from __future__ import annotations

from typing import Any

from app.core.command_runner import SafeCommandRunner


class NvidiaSmiAdapter:
    FULL_FIELDS = [
        "name",
        "driver_version",
        "utilization.gpu",
        "utilization.memory",
        "memory.total",
        "memory.used",
        "memory.free",
        "temperature.gpu",
        "power.draw",
        "power.limit",
        "clocks.current.graphics",
        "clocks.current.memory",
    ]

    FALLBACK_FIELDS = [
        "name",
        "driver_version",
        "utilization.gpu",
        "memory.used",
        "memory.total",
        "temperature.gpu",
    ]

    def __init__(self, runner: SafeCommandRunner, phase1_nvidia: dict[str, Any]) -> None:
        self.runner = runner
        self.phase1 = phase1_nvidia
        self.path = phase1_nvidia.get("nvidia_smi_path") or "nvidia-smi.exe"

    def available(self) -> bool:
        return bool(self.phase1.get("nvidia_smi_available"))

    def telemetry_snapshot(self) -> dict[str, Any]:
        if not self.available():
            return {"ok": False, "source": "phase1", "error": "nvidia-smi was not discovered in Phase 1."}
        result = self._query(self.FULL_FIELDS)
        if result.get("ok"):
            return result
        fallback = self._query(self.FALLBACK_FIELDS)
        fallback["fallback_used"] = True
        return fallback

    def _query(self, fields: list[str]) -> dict[str, Any]:
        query = "--query-gpu=" + ",".join(fields)
        result = self.runner.run([self.path, query, "--format=csv,noheader,nounits"], timeout=10, read_only=True)
        if result.exit_code != 0:
            return {"ok": False, "fields": fields, "command": result.to_dict(), "error": result.stderr or result.error}
        line = next((row.strip() for row in result.stdout.splitlines() if row.strip()), "")
        values = [part.strip() for part in line.split(",")] if line else []
        data = {field: values[index] if index < len(values) else "" for index, field in enumerate(fields)}
        return {"ok": True, "source": "live", "data": data, "fields": fields, "command": result.to_dict()}
