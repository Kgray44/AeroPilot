from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from app.adapters.msi_afterburner_adapter import MsiAfterburnerAdapter
from app.adapters.nvidia_smi_adapter import NvidiaSmiAdapter
from app.adapters.phase1_data_adapter import Phase1Data
from app.adapters.process_adapter import ProcessAdapter
from app.adapters.powercfg_adapter import PowerCfgAdapter
from app.core.app_paths import AppPaths
from app.core.command_runner import SafeCommandRunner
from app.core.config_loader import load_json, save_json_inside_phase4
from app.core.control_surface import ControlSurface


def collect_snapshot(paths: AppPaths | None = None) -> dict[str, Any]:
    app_paths = paths or AppPaths.discover()
    app_paths.ensure_phase4_dirs()
    phase1 = Phase1Data.load(app_paths)
    surface = ControlSurface.load(app_paths)
    runner = SafeCommandRunner(log_file=app_paths.logs_dir / "command_runner.jsonl")

    power = PowerCfgAdapter(runner, phase1.powercfg())
    nvidia = NvidiaSmiAdapter(runner, phase1.nvidia())
    process = ProcessAdapter(runner, phase1.process_targets_seed)
    msi = MsiAfterburnerAdapter(phase1.msi())

    process_matches = process.match_targets()
    return {
        "timestamp_local": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "safety_mode": "READ-ONLY / DRY-RUN",
        "phase": "PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS",
        "active_power_plan": power.active_scheme(),
        "nvidia_smi": nvidia.telemetry_snapshot(),
        "msi_afterburner": msi.status(),
        "process_targets": {
            "matched_targets": [row for row in process_matches if row.get("running_now")],
            "all_targets": process_matches,
        },
        "tool_availability": phase1.summary(),
        "control_surface": {
            "manifest_controls": len(surface.controls),
            "coverage_rows": len(surface.coverage_rows),
            "actions": len(surface.actions),
            "restore_requirements": len(surface.restore_requirements),
        },
        "phase4": {
            "backup_manifest": load_json(app_paths.phase4_root / "backups" / "backup_manifest_latest.json", {}),
            "restore_manifest": load_json(app_paths.phase4_root / "restore" / "restore_manifest_latest.json", {}),
            "sandbox_result": load_json(app_paths.phase4_root / "sandbox" / "sandbox_powercfg_test_result.json", {}),
            "apply_gates": load_json(app_paths.phase4_root / "config" / "apply_gate_config.json", {}),
        },
    }


def write_snapshot(output: Path | None = None) -> Path:
    paths = AppPaths.discover()
    snapshot = collect_snapshot(paths)
    target = output or (paths.raw_outputs_dir / "phase4_snapshot_latest.json")
    return save_json_inside_phase4(target, snapshot, paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect a Phase 4 backup/restore control-surface snapshot.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    path = write_snapshot(args.output)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
