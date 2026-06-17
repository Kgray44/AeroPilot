from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.app_paths import AppPaths
from app.core.config_loader import load_json, load_text


@dataclass
class Phase1Data:
    paths: AppPaths
    report: dict[str, Any]
    discovered_paths: dict[str, Any]
    discovered_capabilities: dict[str, Any]
    risk_catalog: dict[str, Any]
    command_inventory: str
    architecture_notes: str
    process_targets_seed: dict[str, Any]

    @classmethod
    def load(cls, paths: AppPaths | None = None) -> "Phase1Data":
        app_paths = paths or AppPaths.discover()
        root = app_paths.phase1_root
        return cls(
            paths=app_paths,
            report=load_json(root / "phase1_exploration_report.json", {}),
            discovered_paths=load_json(root / "discovered_paths.json", {}),
            discovered_capabilities=load_json(root / "discovered_capabilities.json", {}),
            risk_catalog=load_json(root / "risk_catalog.json", {"items": []}),
            command_inventory=load_text(root / "command_inventory.md"),
            architecture_notes=load_text(root / "future_architecture_notes.md"),
            process_targets_seed=load_json(root / "app_probe" / "process_targets_seed.json", {"targets": []}),
        )

    @property
    def results(self) -> dict[str, Any]:
        return self.report.get("results", {})

    def msi(self) -> dict[str, Any]:
        return self.results.get("msi_afterburner", {})

    def powercfg(self) -> dict[str, Any]:
        return self.results.get("powercfg", {})

    def nvidia(self) -> dict[str, Any]:
        return self.results.get("nvidia_telemetry", {})

    def presentmon(self) -> dict[str, Any]:
        return self.results.get("presentmon", {})

    def librehardwaremonitor(self) -> dict[str, Any]:
        return self.results.get("librehardwaremonitor", {})

    def gigabyte(self) -> dict[str, Any]:
        return self.results.get("gigabyte_controls", {})

    def process_targets(self) -> dict[str, Any]:
        return self.results.get("process_targets", {})

    def cpu_settings(self) -> list[dict[str, Any]]:
        return list(self.powercfg().get("processor_settings", []))

    def risk_items(self) -> list[dict[str, Any]]:
        return list(self.risk_catalog.get("items", []))

    def capabilities(self) -> list[dict[str, Any]]:
        return list(self.discovered_capabilities.get("capabilities", []))

    def summary(self) -> dict[str, Any]:
        msi = self.msi()
        power = self.powercfg()
        nvidia = self.nvidia()
        presentmon = self.presentmon()
        lhm = self.librehardwaremonitor()
        gigabyte = self.gigabyte()
        return {
            "active_power_plan": power.get("active_scheme_name", "unknown"),
            "active_power_plan_guid": power.get("active_scheme_guid"),
            "msi_afterburner_detected": bool(msi.get("installed")),
            "nvidia_smi_detected": bool(nvidia.get("nvidia_smi_available")),
            "presentmon_detected": bool(presentmon.get("presentmon_found")),
            "librehardwaremonitor_detected": bool(lhm.get("found")),
            "gigabyte_detected": bool(gigabyte.get("installed_entries") or gigabyte.get("services")),
            "risk_item_count": len(self.risk_items()),
            "readable_cpu_settings": len([s for s in self.cpu_settings() if s.get("powercfg_can_read")]),
            "process_count_phase1": self.process_targets().get("process_count"),
        }

    def path_status(self, path: str | None) -> dict[str, Any]:
        if not path:
            return {"path": None, "exists": False}
        target = Path(path)
        return {"path": str(target), "exists": target.exists()}
