from __future__ import annotations

from typing import Any


REQUIRED_COMBINED_KEYS = {"name", "description", "phase_status", "cpu", "gpu", "telemetry", "automation"}


def validate_combined_preset(preset: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_COMBINED_KEYS - set(preset.keys()))
    if missing:
        errors.append("Missing keys: " + ", ".join(missing))
    if preset.get("phase_status") not in {"preview_only", "dry_run_only"}:
        errors.append("phase_status must be preview_only or dry_run_only in Phase 2.")
    if preset.get("automation", {}).get("auto_apply") is not False:
        errors.append("automation.auto_apply must be false in Phase 2.")
    gpu = preset.get("gpu", {})
    if gpu.get("slot_verified") is not False:
        errors.append("gpu.slot_verified must be false until Phase 3 manual verification.")
    return errors


def example_combined_preset() -> dict[str, Any]:
    return {
        "name": "BF6 Emergency Preview",
        "description": "Preview-only preset for reducing CPU chaos during BF6.",
        "phase_status": "preview_only",
        "cpu": {
            "power_plan_strategy": "use_existing_or_clone_later",
            "settings": [
                {
                    "friendly_name": "Boost mode",
                    "guid": "be337238-0d82-4146-a960-4f3749d470c7",
                    "ac_value": 0,
                    "dc_value": None,
                    "risk": "Medium",
                }
            ],
        },
        "gpu": {
            "msi_profile_slot": 3,
            "slot_verified": False,
            "risk": "Medium",
        },
        "telemetry": {
            "nvidia_smi": True,
            "presentmon": False,
            "ping_logging": False,
        },
        "automation": {
            "auto_apply": False,
            "restore_on_exit": True,
        },
    }
