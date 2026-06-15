from __future__ import annotations

import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QLabel, QMainWindow, QStatusBar, QTabWidget

from app import APP_NAME
from app.adapters.gigabyte_adapter import GigabyteAdapter
from app.adapters.librehardwaremonitor_adapter import LibreHardwareMonitorAdapter
from app.adapters.msi_afterburner_adapter import MsiAfterburnerAdapter
from app.adapters.nvidia_smi_adapter import NvidiaSmiAdapter
from app.adapters.phase1_data_adapter import Phase1Data
from app.adapters.power_plan_adapter import PowerPlanAdapter
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


class TelemetrySignals(QObject):
    lhm_ready = Signal(dict)


class MainWindow(QMainWindow):
    def __init__(self, paths: Path) -> None:
        super().__init__()
        self.paths = paths
        self.paths.ensure_phase5_dirs()
        self.phase1 = Phase1Data.load(paths)
        self.control_surface = ControlSurface.load(paths)
        self.runner = SafeCommandRunner(log_file=paths.logs_dir / "command_runner.jsonl")
        self.risk_model = RiskModel(paths.phase1_root / "risk_catalog.json")
        gpu_profile_config = load_json(paths.presets_dir / "gpu_profiles.json", {})

        self.power = PowerCfgAdapter(self.runner, self.phase1.powercfg())
        self.power_plans = PowerPlanAdapter(self.runner)
        self.nvidia = NvidiaSmiAdapter(self.runner, self.phase1.nvidia())
        self.msi = MsiAfterburnerAdapter(self.phase1.msi(), gpu_profile_config)
        self.presentmon = PresentMonAdapter(self.runner, self.phase1.presentmon(), paths.raw_outputs_dir / "presentmon")
        self.processes = ProcessAdapter(self.runner, self.phase1.process_targets_seed)
        self.lhm = LibreHardwareMonitorAdapter(self.phase1.librehardwaremonitor(), self.runner, paths.phase4_root)
        self.gigabyte = GigabyteAdapter(self.phase1.gigabyte())
        self.telemetry_signals = TelemetrySignals()
        self.telemetry_signals.lhm_ready.connect(self._apply_lhm_headline)
        self._lhm_busy = False
        self._lhm_last_started = 0.0

        self.setWindowTitle(APP_NAME)
        self.resize(1440, 920)
        self.setMinimumSize(1180, 760)

        tabs = QTabWidget()
        tabs.setObjectName("main_tabs")
        tabs.setDocumentMode(True)
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setUsesScrollButtons(True)
        tabs.addTab(DashboardTab(self), "Dashboard")
        tabs.addTab(CpuTab(self), "CPU Presets")
        tabs.addTab(GpuTab(self), "GPU Profiles")
        tabs.addTab(TelemetryTab(self), "Sensors")
        tabs.addTab(GameAutomationTab(self), "Game Automation")
        tabs.addTab(AutoTuningTab(self), "Auto Tuning")
        tabs.addTab(FanExperimentalTab(self), "Fan / Experimental")
        tabs.addTab(LogsTab(self), "Logs")
        tabs.addTab(SettingsSafetyTab(self), "Settings")
        self.setCentralWidget(tabs)
        self.tabs = tabs

        self.telemetry_bar = QStatusBar()
        self.telemetry_bar.setObjectName("always_visible_telemetry_strip")
        self.gpu_label = QLabel("GPU: reading...")
        self.vram_label = QLabel("VRAM: reading...")
        self.cpu_label = QLabel("CPU: reading...")
        self.fps_label = QLabel("FPS: idle")
        self.telemetry_bar.addPermanentWidget(self.gpu_label, 2)
        self.telemetry_bar.addPermanentWidget(self.vram_label, 2)
        self.telemetry_bar.addPermanentWidget(self.cpu_label, 2)
        self.telemetry_bar.addPermanentWidget(self.fps_label, 1)
        self.setStatusBar(self.telemetry_bar)

        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.setInterval(5000)
        self.telemetry_timer.timeout.connect(self.refresh_top_telemetry)
        self.telemetry_timer.start()
        self.refresh_top_telemetry()

    def refresh_top_telemetry(self) -> None:
        try:
            gpu = self.nvidia.telemetry_snapshot()
            if gpu.get("ok"):
                data = gpu.get("data", {})
                self.gpu_label.setText(
                    f"GPU {data.get('temperature.gpu', 'n/a')} C | {data.get('utilization.gpu', 'n/a')}% | {data.get('power.draw', 'n/a')} W"
                )
                self.vram_label.setText(f"VRAM {data.get('memory.used', 'n/a')} / {data.get('memory.total', 'n/a')} MB")
            else:
                self.gpu_label.setText("GPU nvidia-smi unavailable")
                self.vram_label.setText("VRAM n/a")
        except Exception as exc:
            self.gpu_label.setText(f"GPU read error: {exc}")
            self.vram_label.setText("VRAM n/a")

        try:
            if not self._lhm_busy and time.monotonic() - self._lhm_last_started > 30:
                self._lhm_busy = True
                self._lhm_last_started = time.monotonic()
                threading.Thread(target=self._read_lhm_background, daemon=True).start()
        except Exception as exc:
            self.cpu_label.setText(f"CPU sensor error: {exc}")

        try:
            self.fps_label.setText(self.presentmon.headline())
        except Exception:
            self.fps_label.setText("FPS idle")

    def _read_lhm_background(self) -> None:
        try:
            snapshot = self.lhm.sensor_snapshot()
            headline = self.lhm.headline(snapshot)
            headline["ok"] = bool(snapshot.get("ok"))
            headline["error"] = snapshot.get("error")
        except Exception as exc:
            headline = {"ok": False, "CPU": "LHM error", "Fan": "Fan n/a", "Sensors": str(exc), "error": str(exc)}
        self.telemetry_signals.lhm_ready.emit(headline)

    def _apply_lhm_headline(self, headline: dict) -> None:
        self._lhm_busy = False
        if headline.get("ok"):
            self.cpu_label.setText(headline.get("status_display", "CPU telemetry unavailable"))
        else:
            self.cpu_label.setText(headline.get("status_display", "CPU telemetry unavailable"))

    def closeEvent(self, event) -> None:
        try:
            self.presentmon.cleanup_on_close()
        except Exception:
            pass
        super().closeEvent(event)
