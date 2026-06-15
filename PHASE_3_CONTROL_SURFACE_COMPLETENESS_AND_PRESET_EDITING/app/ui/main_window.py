from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QTabWidget

from app import APP_NAME
from app.adapters.gigabyte_adapter import GigabyteAdapter
from app.adapters.librehardwaremonitor_adapter import LibreHardwareMonitorAdapter
from app.adapters.msi_afterburner_adapter import MsiAfterburnerAdapter
from app.adapters.nvidia_smi_adapter import NvidiaSmiAdapter
from app.adapters.phase1_data_adapter import Phase1Data
from app.adapters.powercfg_adapter import PowerCfgAdapter
from app.adapters.presentmon_adapter import PresentMonAdapter
from app.adapters.process_adapter import ProcessAdapter
from app.core.command_runner import SafeCommandRunner
from app.core.config_loader import load_json
from app.core.control_surface import ControlSurface
from app.core.risk_model import RiskModel
from app.ui.autotuning_tab import AutoTuningTab
from app.ui.cpu_tab import CpuTab
from app.ui.dashboard_tab import DashboardTab
from app.ui.fan_experimental_tab import FanExperimentalTab
from app.ui.game_automation_tab import GameAutomationTab
from app.ui.gpu_tab import GpuTab
from app.ui.logs_tab import LogsTab
from app.ui.settings_safety_tab import SettingsSafetyTab
from app.ui.telemetry_tab import TelemetryTab


class MainWindow(QMainWindow):
    def __init__(self, paths: Path) -> None:
        super().__init__()
        self.paths = paths
        self.paths.ensure_phase3_dirs()
        self.phase1 = Phase1Data.load(paths)
        self.control_surface = ControlSurface.load(paths)
        self.runner = SafeCommandRunner(log_file=paths.logs_dir / "command_runner.jsonl")
        self.risk_model = RiskModel(paths.phase1_root / "risk_catalog.json")
        gpu_profile_config = load_json(paths.presets_dir / "gpu_profiles.json", {})

        self.power = PowerCfgAdapter(self.runner, self.phase1.powercfg())
        self.nvidia = NvidiaSmiAdapter(self.runner, self.phase1.nvidia())
        self.msi = MsiAfterburnerAdapter(self.phase1.msi(), gpu_profile_config)
        self.presentmon = PresentMonAdapter(self.runner, self.phase1.presentmon())
        self.processes = ProcessAdapter(self.runner, self.phase1.process_targets_seed)
        self.lhm = LibreHardwareMonitorAdapter(self.phase1.librehardwaremonitor())
        self.gigabyte = GigabyteAdapter(self.phase1.gigabyte())

        self.setWindowTitle(APP_NAME)
        self.resize(1280, 820)

        tabs = QTabWidget()
        tabs.addTab(DashboardTab(self), "Dashboard")
        tabs.addTab(CpuTab(self), "CPU Presets")
        tabs.addTab(GpuTab(self), "GPU Profiles")
        tabs.addTab(TelemetryTab(self), "Sensors / Telemetry")
        tabs.addTab(GameAutomationTab(self), "Game Automation")
        tabs.addTab(AutoTuningTab(self), "Auto Tuning")
        tabs.addTab(FanExperimentalTab(self), "Fan Control / Experimental")
        tabs.addTab(LogsTab(self), "Logs")
        tabs.addTab(SettingsSafetyTab(self), "Settings / Safety")
        self.setCentralWidget(tabs)
