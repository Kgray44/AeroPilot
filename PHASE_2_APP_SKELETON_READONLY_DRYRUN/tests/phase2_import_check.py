from __future__ import annotations

from app.adapters.phase1_data_adapter import Phase1Data
from app.adapters.msi_afterburner_adapter import MsiAfterburnerAdapter
from app.core.app_paths import AppPaths
from app.core.command_runner import SafeCommandRunner
from app.core.dryrun import msi_profile_preview
from app.core.preset_schema import example_combined_preset, validate_combined_preset
from app.core.risk_model import RiskModel


def main() -> int:
    paths = AppPaths.discover()
    phase1 = Phase1Data.load(paths)
    assert phase1.summary()["risk_item_count"] > 0
    risk = RiskModel(paths.phase1_root / "risk_catalog.json")
    assert risk.get_risk_for_control("MSI profile slot launch") in {"Medium", "Unknown"}
    preview = msi_profile_preview("MSIAfterburner.exe", 1)
    assert preview.dry_run if hasattr(preview, "dry_run") else True
    adapter = MsiAfterburnerAdapter(phase1.msi())
    assert len(adapter.slots()) == 5
    assert validate_combined_preset(example_combined_preset()) == []
    runner = SafeCommandRunner()
    dry = runner.run(["example.exe", "--write"], dry_run=True, read_only=False)
    assert not dry.executed
    print("phase2 import check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
