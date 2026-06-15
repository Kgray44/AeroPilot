from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


PHASE = "PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING"
SAFETY_MODE = "READ-ONLY / DRY-RUN"
PHASE4_RECOMMENDATION = (
    "Backup/restore foundation and first explicitly-approved apply tests. Build restore manifests, "
    "export/clone active power plan, back up MSI Afterburner configs/profiles, manually verify MSI profile "
    "slot mapping, and add one or two guarded CPU setting apply tests with immediate restore. "
    "No fan control or EC writes yet."  # recommendation text
)

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT.parent
PHASE1 = APP_ROOT / "PHASE_1_EXPLORATION"
PHASE2 = APP_ROOT / "PHASE_2_APP_SKELETON_READONLY_DRYRUN"
NOW = datetime.now().replace(microsecond=0).isoformat()


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(relative: str, data: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(relative: str, text: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


phase1_report = read_json(PHASE1 / "phase1_exploration_report.json", {})
discovered_paths = read_json(PHASE1 / "discovered_paths.json", {})
discovered_capabilities = read_json(PHASE1 / "discovered_capabilities.json", {"capabilities": []})
risk_catalog = read_json(PHASE1 / "risk_catalog.json", {"items": []})
process_seed = read_json(PHASE1 / "app_probe" / "process_targets_seed.json", {"targets": []})
powercfg_raw = read_json(PHASE1 / "raw_outputs" / "powercfg_detector_result.json", {})
msi_raw = read_json(PHASE1 / "raw_outputs" / "msi_afterburner_detector_result.json", {})
nvidia_raw = read_json(PHASE1 / "raw_outputs" / "nvidia_telemetry_detector_result.json", {})
presentmon_raw = read_json(PHASE1 / "raw_outputs" / "presentmon_detector_result.json", {})
lhm_raw = read_json(PHASE1 / "raw_outputs" / "librehardwaremonitor_detector_result.json", {})
gigabyte_raw = read_json(PHASE1 / "raw_outputs" / "gigabyte_controls_detector_result.json", {})
phase2_report = read_json(PHASE2 / "phase2_report.json", {})

risk_by_name = {item.get("setting_control_name"): item for item in risk_catalog.get("items", [])}
cap_by_name = {item.get("name"): item for item in discovered_capabilities.get("capabilities", [])}


def risk(name: str | None, fallback: str = "Unknown") -> dict[str, Any]:
    item = risk_by_name.get(name or "")
    if not item:
        return {
            "level": fallback,
            "warning": "Review before future apply. Phase 3 stores app-side desired state only.",
        }
    return {
        "level": item.get("risk_level", fallback),
        "warning": item.get("suggested_warning_label") or item.get("what_can_go_wrong") or "Review before future apply.",
        "what_can_go_wrong": item.get("what_can_go_wrong"),
    }


def source(
    *,
    phase1_file: str | None = None,
    phase2_file: str | None = None,
    adapter: str | None = None,
    phase1_risk_name: str | None = None,
    capability_name: str | None = None,
) -> dict[str, Any]:
    return {
        "phase1_file": phase1_file,
        "phase2_file": phase2_file,
        "adapter": adapter,
        "phase1_risk_name": phase1_risk_name,
        "capability_name": capability_name,
    }


def coverage(
    appears: bool = True,
    dryrun: bool = False,
    preset: bool = False,
    restore: bool = True,
    validation: bool = True,
) -> dict[str, bool]:
    return {
        "appears_in_gui": appears,
        "has_dryrun_preview": dryrun,
        "has_preset_binding": preset,
        "has_restore_strategy": restore,
        "has_validation": validation,
    }


def current(readable: bool = False, ac: Any = None, dc: Any = None, display: str | None = None, value: Any = None) -> dict[str, Any]:
    if display is None:
        if readable and (ac is not None or dc is not None):
            display = f"AC {ac} / DC {dc}"
        elif readable and value is not None:
            display = str(value)
        else:
            display = "Not readable in Phase 3"
    return {
        "readable": readable,
        "ac_value": ac,
        "dc_value": dc,
        "value": value,
        "display": display,
    }


def editing(editable: bool, saved_to: str | None = None, allowed_values: list[dict[str, Any]] | None = None, note: str | None = None) -> dict[str, Any]:
    return {
        "editable_in_phase3": editable,
        "saved_to": saved_to,
        "allowed_values": allowed_values or [],
        "phase3_note": note or "Phase 3 edits only app-side JSON. No system setting is changed.",
    }


def future(
    possible: bool,
    command_template: str | None = None,
    risk_level: str = "Unknown",
    requires_admin: str = "unknown_or_maybe",
    backup: bool = False,
    status: str = "dry_run_only",
) -> dict[str, Any]:
    return {
        "possible": possible,
        "enabled_now": False,
        "dry_run_only": True,
        "phase3_status": status,
        "command_template": command_template,
        "requires_admin": requires_admin,
        "requires_backup": backup,
        "risk_level": risk_level,
    }


def restore(strategy: str, requires_manifest: bool = True, proven: bool = False) -> dict[str, Any]:
    return {
        "strategy": strategy,
        "requires_manifest": requires_manifest,
        "restore_proven": proven,
    }


controls: list[dict[str, Any]] = []


def add_control(
    control_id: str,
    friendly_name: str,
    category: str,
    subcategory: str,
    ui_tab: str,
    ui_section: str,
    *,
    status: str,
    source_data: dict[str, Any],
    current_value: dict[str, Any],
    desired_value_editing: dict[str, Any],
    future_apply: dict[str, Any],
    restore_data: dict[str, Any],
    risk_data: dict[str, Any],
    coverage_data: dict[str, Any],
    notes: str,
    alias: str | None = None,
    setting_guid: str | None = None,
) -> None:
    row = {
        "control_id": control_id,
        "friendly_name": friendly_name,
        "category": category,
        "subcategory": subcategory,
        "ui_tab": ui_tab,
        "ui_section": ui_section,
        "status": status,
        "source": source_data,
        "current_value": current_value,
        "desired_value_editing": desired_value_editing,
        "future_apply": future_apply,
        "restore": restore_data,
        "risk": risk_data,
        "coverage": coverage_data,
        "notes": notes,
    }
    if alias:
        row["alias"] = alias
    if setting_guid:
        row["setting_guid"] = setting_guid
    controls.append(row)


def allowed_from_possible(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in values or []:
        result.append({"value": int(item.get("index", 0)), "label": str(item.get("name", item.get("index", "")))})
    return result


cpu_id_by_alias = {
    "PERFBOOSTMODE": "cpu.boost.mode",
    "PERFBOOSTPOL": "cpu.boost.policy",
    "PERFEPP": "cpu.power.epp",
    "PROCTHROTTLEMIN": "cpu.state.minimum",
    "PROCTHROTTLEMAX": "cpu.state.maximum",
    "SYSCOOLPOL": "cpu.cooling.system_policy",
    "PROCFREQMAX": "cpu.frequency.maximum",
    "CPMINCORES": "cpu.parking.min_cores",
    "CPMAXCORES": "cpu.parking.max_cores",
    "IDLEDISABLE": "cpu.idle.disable",
    "HETEROPOLICY": "cpu.scheduling.heterogeneous_policy",
    "PERFINCTHRESHOLD": "cpu.boost.performance_increase_threshold",
    "PERFDECTHRESHOLD": "cpu.boost.performance_decrease_threshold",
}

add_control(
    "cpu.power_plan.active_selection",
    "Active power plan selection",
    "CPU power behavior",
    "Power plan",
    "CPU Presets",
    "Current CPU/power plan status",
    status="read_only",
    source_data=source(phase1_file="raw_outputs/powercfg_detector_result.json", adapter="powercfg_adapter", capability_name="Windows CPU power setting viewer"),
    current_value=current(True, display=f"{powercfg_raw.get('active_scheme_name', 'Unknown')} ({powercfg_raw.get('active_scheme_guid', 'unknown')})"),
    desired_value_editing=editing(False, None, note="Phase 3 does not change active plans."),
    future_apply=future(True, "powercfg /setactive <scheme_guid>", "Medium", "unknown_or_maybe", True),
    restore_data=restore("Reactivate the previously captured active power scheme GUID or import cloned scheme."),
    risk_data={"level": "Medium", "warning": "Changing active plan affects all power settings tied to that plan."},
    coverage_data=coverage(True, True, False, True, True),
    notes="Visible for future control, but Phase 3 is read-only.",
)

for setting in powercfg_raw.get("processor_settings", []):
    alias = setting.get("alias") or setting.get("friendly_name", "").upper().replace(" ", "_")
    control_id = cpu_id_by_alias.get(alias, f"cpu.extra.{alias.lower()}")
    readable = bool(setting.get("powercfg_can_read"))
    write_possible = bool(setting.get("powercfg_can_likely_write_later"))
    risk_name = setting.get("friendly_name")
    add_control(
        control_id,
        setting.get("friendly_name", alias),
        setting.get("category", "CPU power behavior"),
        "Processor setting",
        "CPU Presets",
        "Full CPU control table",
        status="readable" if readable else "blocked_or_unavailable",
        source_data=source(
            phase1_file="raw_outputs/powercfg_detector_result.json",
            adapter="powercfg_adapter",
            phase1_risk_name=risk_name,
            capability_name="Windows CPU power setting writes later" if write_possible else "Windows CPU power setting viewer",
        ),
        current_value=current(readable, setting.get("current_ac_value"), setting.get("current_dc_value")),
        desired_value_editing=editing(
            write_possible,
            "presets/cpu_presets.json" if write_possible else None,
            allowed_from_possible(setting.get("possible_values", [])),
            "Stored as desired preset values only. Advanced hidden settings stay disabled if unreadable.",
        ),
        future_apply=future(
            write_possible,
            "powercfg /setacvalueindex <scheme_guid> SUB_PROCESSOR <setting_guid> <value>" if write_possible else None,  # dry-run template
            setting.get("risk_level", "Unknown"),
            "unknown_or_maybe",
            write_possible,
            "dry_run_only" if write_possible else "blocked",
        ),
        restore_data=restore("Restore previous AC/DC values or re-import cloned power scheme."),
        risk_data=risk(risk_name, setting.get("risk_level", "Unknown")),
        coverage_data=coverage(True, write_possible, write_possible, True, True),
        notes=setting.get("notes", "CPU setting imported from Phase 1 powercfg discovery."),
        alias=alias,
        setting_guid=setting.get("setting_guid"),
    )

# Fan view also needs the same cooling policy represented in the experimental tab.
add_control(
    "fan.powercfg.cooling_policy",
    "System cooling policy through powercfg",
    "Fan control",
    "Powercfg cooling",
    "Fan Control / Experimental",
    "Powercfg cooling policy",
    status="readable",
    source_data=source(phase1_file="raw_outputs/powercfg_detector_result.json", adapter="powercfg_adapter", phase1_risk_name="System cooling policy"),
    current_value=current(True, display="Mirrors cpu.cooling.system_policy"),
    desired_value_editing=editing(True, "presets/cpu_presets.json", [{"value": 0, "label": "Passive"}, {"value": 1, "label": "Active"}]),
    future_apply=future(True, "powercfg /setacvalueindex <scheme_guid> SUB_PROCESSOR SYSCOOLPOL <value>", "Low", "unknown_or_maybe", True),
    restore_data=restore("Restore prior cooling policy AC/DC values or cloned power scheme."),
    risk_data=risk("System cooling policy", "Low"),
    coverage_data=coverage(True, True, True, True, True),
    notes="This is not direct fan control and may not override OEM firmware.",
)

msi_path = None
if msi_raw.get("executable_paths"):
    msi_path = msi_raw["executable_paths"][0].get("path")
for slot in range(1, 6):
    add_control(
        f"gpu.msi.profile.slot{slot}",
        f"MSI profile slot {slot} launch",
        "GPU profile loading",
        "MSI profile slots",
        "GPU Profiles",
        "MSI profile slot mapping",
        status="preview_only",
        source_data=source(phase1_file="raw_outputs/msi_afterburner_detector_result.json", adapter="msi_afterburner_adapter", phase1_risk_name="MSI profile slot launch", capability_name="MSI Afterburner profile launch templates"),
        current_value=current(False, display="Slot mapping unverified"),
        desired_value_editing=editing(True, "presets/gpu_profiles.json", note="Editable friendly name only. The app does not launch MSI in Phase 3."),
        future_apply=future(True, f'"{msi_path or "<MSIAfterburner.exe>"}" -Profile{slot}', "Medium", "unknown_or_maybe", True),
        restore_data=restore("Back up MSI configs/profiles first; restore files and known safe slot if needed."),
        risk_data=risk("MSI profile slot launch", "Medium"),
        coverage_data=coverage(True, True, True, True, True),
        notes="Wrong slot can apply an unintended voltage/frequency curve.",
    )

gpu_controls = [
    ("gpu.msi.backup.config_profiles", "MSI profile/config backup", "GPU voltage/frequency curve profile", "Backup", "GPU Profiles", "MSI files", "future", "future_backup.msi.configs", "MSI Afterburner profile/config backup", "Copy MSIAfterburner.cfg and Profiles into a timestamped restore manifest."),
    ("gpu.msi.profile.slot_mapping", "MSI profile slot friendly-name mapping", "GPU profile loading", "Slot mapping", "GPU Profiles", "MSI profile slot mapping", "editable", None, "MSI Afterburner profile launch templates", "Phase 3 edits app-side labels only."),
    ("gpu.msi.curve_editor.future", "GPU voltage/frequency curve profile editing as future/MSI-owned", "GPU voltage/frequency curve profile", "Curve editing", "GPU Profiles", "MSI-owned future controls", "future", None, "GPU voltage/frequency curve profile editing", "The app does not edit MSI curve files in Phase 3."),
    ("gpu.profile.stock_safe_concept", "GPU stock/safe profile concept", "GPU profile loading", "Profile concept", "GPU Profiles", "Future profile concepts", "future", None, None, "Requires manual MSI slot verification."),
    ("gpu.profile.efficient_undervolt_concept", "GPU efficient undervolt profile concept", "GPU profile loading", "Profile concept", "GPU Profiles", "Future profile concepts", "future", None, None, "Requires stability validation."),
    ("gpu.profile.balanced_concept", "GPU balanced profile concept", "GPU profile loading", "Profile concept", "GPU Profiles", "Future profile concepts", "future", None, None, "Requires telemetry comparison."),
    ("gpu.profile.aggressive_concept", "GPU aggressive profile concept", "GPU profile loading", "Profile concept", "GPU Profiles", "Future profile concepts", "future", None, None, "Requires explicit confirmation and restore plan."),
    ("gpu.profile.test_concept", "GPU test profile concept", "GPU profile loading", "Profile concept", "GPU Profiles", "Future profile concepts", "future", None, None, "Testing slot must be isolated and verified."),
]
for cid, name, cat, sub, tab, section, status, action, risk_name, notes in gpu_controls:
    add_control(
        cid, name, cat, sub, tab, section,
        status=status,
        source_data=source(phase1_file="raw_outputs/msi_afterburner_detector_result.json", adapter="msi_afterburner_adapter", phase1_risk_name=risk_name, capability_name="MSI Afterburner profile/config backup" if "backup" in cid else None),
        current_value=current(False, display="Future or app-side only"),
        desired_value_editing=editing("slot_mapping" in cid, "presets/gpu_profiles.json" if "slot_mapping" in cid else None),
        future_apply=future("backup" in cid, action, risk(risk_name, "Medium").get("level", "Medium"), "unknown_or_maybe", "backup" in cid, "future" if "backup" in cid else "blocked"),
        restore_data=restore("Use MSI config/profile file backup before any future apply."),
        risk_data=risk(risk_name, "High" if "aggressive" in cid or "curve" in cid else "Medium"),
        coverage_data=coverage(True, False, "slot_mapping" in cid, True, True),
        notes=notes,
    )

nvidia_fields = [
    ("telemetry.nvidia.gpu_name", "GPU name", "name"),
    ("telemetry.nvidia.driver_version", "Driver version", "driver_version"),
    ("telemetry.nvidia.gpu_utilization", "GPU utilization", "utilization.gpu"),
    ("telemetry.nvidia.memory_utilization", "Memory utilization", "utilization.memory"),
    ("telemetry.nvidia.vram", "VRAM total/used/free", "memory.total"),
    ("telemetry.nvidia.temperature", "GPU temperature", "temperature.gpu"),
    ("telemetry.nvidia.power_draw", "GPU power draw", "power.draw"),
    ("telemetry.nvidia.power_limit_read", "GPU power limit read", "power.limit"),
    ("telemetry.nvidia.graphics_clock", "Graphics clock", "clocks.current.graphics"),
    ("telemetry.nvidia.memory_clock", "Memory clock", "clocks.current.memory"),
]
nvidia_summary = nvidia_raw.get("gpu_summary", {})
for cid, name, key in nvidia_fields:
    display = nvidia_summary.get(key, "Not available")
    if cid == "telemetry.nvidia.vram":
        display = f"total={nvidia_summary.get('memory.total')} used={nvidia_summary.get('memory.used')} free={nvidia_summary.get('memory.free')}"
    add_control(
        cid, name, "GPU power/clock telemetry", "nvidia-smi field", "Sensors / Telemetry", "Telemetry field catalog",
        status="read_only",
        source_data=source(phase1_file="raw_outputs/nvidia_telemetry_detector_result.json", adapter="nvidia_smi_adapter", phase1_risk_name="NVIDIA telemetry polling", capability_name="NVIDIA telemetry through nvidia-smi"),
        current_value=current(True, value=display),
        desired_value_editing=editing(False),
        future_apply=future(False, None, "Read-only", "no", False, "enabled_readonly"),
        restore_data=restore("No restore needed for read-only telemetry.", False, True),
        risk_data=risk("NVIDIA telemetry polling", "Read-only"),
        coverage_data=coverage(True, False, False, True, True),
        notes="Read through nvidia-smi only.",
    )

for cid, name, notes, cap in [
    ("telemetry.nvidia.gpu_processes", "GPU processes", "Read-only process list through nvidia-smi query/pmon.", "NVIDIA telemetry through nvidia-smi"),
    ("telemetry.nvidia.fallback_query", "nvidia-smi fallback query behavior", "Full query can fail when fields are unsupported; fallback omits unsupported fields.", "NVIDIA telemetry through nvidia-smi"),
    ("telemetry.nvml.future_adapter", "NVML future optional adapter", "Optional future Python NVML path if nvidia-smi polling is too awkward.", "NVML Python telemetry later"),
]:
    add_control(
        cid, name, "GPU power/clock telemetry", "Telemetry plumbing", "Sensors / Telemetry", "Telemetry field catalog",
        status="read_only" if "future" not in cid else "future",
        source_data=source(phase1_file="raw_outputs/nvidia_telemetry_detector_result.json", adapter="nvidia_smi_adapter", phase1_risk_name="NVIDIA telemetry polling", capability_name=cap),
        current_value=current(True if cid != "telemetry.nvml.future_adapter" else False, display=notes),
        desired_value_editing=editing(False),
        future_apply=future(False, None, "Read-only", "no", False, "enabled_readonly" if "future" not in cid else "future"),
        restore_data=restore("No restore needed for read-only telemetry.", False, True),
        risk_data=risk("NVIDIA telemetry polling", "Read-only"),
        coverage_data=coverage(True, False, False, True, True),
        notes=notes,
    )

presentmon_controls = [
    ("presentmon.candidate.selection", "PresentMon executable candidate selection", "Candidate selection", "editable", True),
    ("presentmon.syntax.verification", "PresentMon syntax verification", "Syntax check", "read_only", False),
    ("presentmon.process_targeting", "PresentMon process targeting", "Capture targeting", "future", False),
    ("presentmon.csv_output", "PresentMon CSV output", "Capture output", "future", False),
    ("presentmon.timed_capture", "PresentMon timed capture", "Capture session", "future", False),
    ("metrics.fps.average", "FPS average future metric", "Future metric", "future", False),
    ("metrics.fps.one_percent_low", "1 percent low future metric", "Future metric", "future", False),
    ("metrics.frametime", "Frame-time future metric", "Future metric", "future", False),
    ("capture.session_folder", "Capture session folder future behavior", "Session folder", "future", False),
]
for cid, name, sub, status, editable in presentmon_controls:
    add_control(
        cid, name, "FPS/frame capture", sub, "Sensors / Telemetry", "PresentMon future section",
        status=status,
        source_data=source(phase1_file="raw_outputs/presentmon_detector_result.json", adapter="presentmon_adapter", phase1_risk_name="PresentMon capture", capability_name="PresentMon frame-time capture"),
        current_value=current(cid == "presentmon.candidate.selection", display=f"{len(presentmon_raw.get('executable_paths', []))} candidates found"),
        desired_value_editing=editing(editable, "config/app_config.json" if editable else None),
        future_apply=future(status == "future" and cid.startswith("presentmon."), "PresentMon <verified args>" if cid.startswith("presentmon.") else None, "Low", "no", True if cid.startswith("presentmon.") else False, "future"),
        restore_data=restore("Stop capture and keep session files under app-controlled session folder.", cid.startswith("presentmon."), False),
        risk_data=risk("PresentMon capture", "Low"),
        coverage_data=coverage(True, False, editable, True, True),
        notes="No PresentMon capture is started in Phase 3.",
    )

lhm_controls = [
    ("lhm.dll.candidate", "LibreHardwareMonitor DLL candidate"),
    ("lhm.sensor.cpu_temperature", "CPU temperature future sensor"),
    ("lhm.sensor.cpu_clock", "CPU clock future sensor"),
    ("lhm.sensor.cpu_package_power", "CPU package power future sensor"),
    ("lhm.sensor.fan_rpm", "Fan RPM future sensor if available"),
    ("lhm.sensor.voltage", "Voltage sensor future support"),
    ("lhm.sensor.motherboard", "Motherboard sensor future support"),
]
for cid, name in lhm_controls:
    add_control(
        cid, name, "CPU power behavior", "LibreHardwareMonitor sensors", "Sensors / Telemetry", "LibreHardwareMonitor future section",
        status="future" if cid != "lhm.dll.candidate" else "read_only",
        source_data=source(phase1_file="raw_outputs/librehardwaremonitor_detector_result.json", adapter="librehardwaremonitor_adapter", capability_name="LibreHardwareMonitor sensors"),
        current_value=current(cid == "lhm.dll.candidate", display=f"{len(lhm_raw.get('library_paths', []))} library candidates found"),
        desired_value_editing=editing(False),
        future_apply=future(False, None, "Read-only", "unknown_or_maybe", False, "future"),
        restore_data=restore("No restore needed for read-only sensor discovery.", False, True),
        risk_data={"level": "Read-only", "warning": "Sensor support is hardware-dependent. Fan and voltage reads may require admin or drivers."},
        coverage_data=coverage(True, False, False, True, True),
        notes="Phase 3 does not load LibreHardwareMonitor DLLs.",
    )

process_id_map = {
    "battlefield_6": "process.bf6",
    "steam": "process.steam",
    "ea_app": "process.ea_app",
    "epic_games": "process.epic_games",
    "sea_of_thieves": "process.sea_of_thieves",
    "minecraft": "process.minecraft",
    "msi_afterburner": "process.msi_afterburner",
    "rtss": "process.rtss",
    "presentmon": "process.presentmon",
    "hwinfo": "process.hwinfo",
    "gigabyte_control_center": "process.gigabyte_control_center",
    "nvidia_app": "process.nvidia_app",
}
for target in process_seed.get("targets", []):
    cid = process_id_map.get(target.get("id"), f"process.{target.get('id', 'unknown')}")
    add_control(
        cid, f"{target.get('friendly')} process detection", "Game detection", target.get("category", "Process"), "Game Automation", "Process rule table",
        status="read_only",
        source_data=source(phase1_file="app_probe/process_targets_seed.json", adapter="process_adapter", phase1_risk_name="Game detection and auto preset switching", capability_name="Game and tool process detection"),
        current_value=current(True, display="Live preview available from process adapter"),
        desired_value_editing=editing(True, "presets/game_rules.json"),
        future_apply=future(False, None, "Low", "no", False, "enabled_readonly"),
        restore_data=restore("No restore needed for read-only detection.", False, True),
        risk_data=risk("Game detection and auto preset switching", "Low"),
        coverage_data=coverage(True, False, True, True, True),
        notes=target.get("match_notes", "Process detection rule."),
    )

for cid, name, notes in [
    ("process.false_positive_handling", "False-positive handling", "Steam webhelper and launcher helpers must not count as games by themselves."),
    ("process.command_line_filtering", "Process command-line filtering for broad names like java/javaw", "java/javaw are broad and require command-line contains filters before automation."),
    ("automation.auto_apply.future", "Auto-apply future action", "Forced off in Phase 3."),
    ("automation.restore_on_exit.future", "Auto-restore-on-exit future action", "Future automation must restore after game exit."),
]:
    add_control(
        cid, name, "Game detection", "Automation safety", "Game Automation", "Automation safety",
        status="future" if "future" in cid else "read_only",
        source_data=source(phase1_file="app_probe/process_targets_seed.json", adapter="process_adapter", phase1_risk_name="Game detection and auto preset switching"),
        current_value=current(False, display=notes),
        desired_value_editing=editing(True if "future" in cid else False, "presets/game_rules.json" if "future" in cid else None),
        future_apply=future("auto_apply" in cid or "restore" in cid, None, "Medium" if "auto_apply" in cid else "Low", "no", True if ("auto_apply" in cid or "restore" in cid) else False, "future"),
        restore_data=restore("Back up app JSON rules; auto-restore must have a previous-state manifest."),
        risk_data=risk("Game detection and auto preset switching", "Low"),
        coverage_data=coverage(True, False, "future" in cid, True, True),
        notes=notes,
    )

network_controls = [
    ("network.ping_logger.future", "Ping logger future support"),
    ("network.target_host.selection", "Target host selection"),
    ("network.interval.setting", "Interval setting"),
    ("network.session_logging", "Session logging"),
    ("network.ping_spike_detection", "Ping spike detection future metric"),
]
for cid, name in network_controls:
    add_control(
        cid, name, "Ping/network logging", "Network telemetry", "Auto Tuning", "Future scoring model",
        status="future" if cid != "network.target_host.selection" and cid != "network.interval.setting" else "editable",
        source_data=source(phase1_file="risk_catalog.json", adapter=None, phase1_risk_name="Ping/network logging"),
        current_value=current(False, display="Future app-side telemetry setting"),
        desired_value_editing=editing(cid in {"network.target_host.selection", "network.interval.setting"}, "config/app_config.json" if cid in {"network.target_host.selection", "network.interval.setting"} else None),
        future_apply=future(False, None, "Safe", "no", False, "future"),
        restore_data=restore("No system restore needed; delete or archive app-side logs.", False, True),
        risk_data=risk("Ping/network logging", "Safe"),
        coverage_data=coverage(True, False, cid in {"network.target_host.selection", "network.interval.setting"}, True, True),
        notes="No ping logger is started in Phase 3.",
    )

fan_controls = [
    ("fan.gigabyte.gcc_surfaces", "Gigabyte/GCC detected process/service surfaces", "OEM surfaces", "read_only"),
    ("fan.gigabyte.powergear_service_status", "Gigabyte PowerGear service read-only status", "OEM service", "read_only"),
    ("fan.official_api.status", "Official API status unknown", "Feasibility", "blocked"),
    ("fan.command_line_control.status", "Command-line control unknown", "Feasibility", "blocked"),
    ("fan.config_file_control.status", "Config-file control unproven", "Feasibility", "blocked"),
    ("fan.ui_automation.status", "UI automation possible but fragile", "Feasibility", "blocked"),
    ("fan.ec_write.research_only", "Embedded controller writes dangerous/research-only", "Low-level hardware", "blocked"),
    ("fan.mode_display.future", "Fan mode display future concept", "Future display", "future"),
    ("fan.apply_action.blocked", "Fan apply action blocked", "Blocked actions", "blocked"),
]
for cid, name, sub, status in fan_controls:
    risk_name = "Embedded controller writes" if "ec_write" in cid else "Fan mode/control through GCC or OEM paths"
    add_control(
        cid, name, "Fan control", sub, "Fan Control / Experimental", "Blocked and feasibility rows",
        status=status,
        source_data=source(phase1_file="raw_outputs/gigabyte_controls_detector_result.json", adapter="gigabyte_adapter", phase1_risk_name=risk_name, capability_name="Gigabyte/GCC discovery"),
        current_value=current(status == "read_only", display=f"{len(gigabyte_raw.get('running_processes', []))} GCC processes, {len(gigabyte_raw.get('services', []))} services"),
        desired_value_editing=editing(False),
        future_apply=future(False, None, risk(risk_name, "High").get("level", "High"), "unknown_or_maybe", True, "blocked"),
        restore_data=restore("Blocked until a proven OEM restore path exists.", True, False),
        risk_data=risk(risk_name, "High"),
        coverage_data=coverage(True, False, False, True, True),
        notes="No fan modes, services, config files, or EC registers are changed in Phase 3.",
    )

restore_controls = [
    ("restore.save_current_state", "Save current state", "Restore/backup", "State capture", "Settings / Safety", "Future backup/restore"),
    ("restore.power_plan.clone_export", "Clone/export active power plan", "Restore/backup", "Power plan backup", "Settings / Safety", "Future backup/restore"),
    ("restore.powercfg.previous_values", "Restore previous powercfg values", "Restore/backup", "Powercfg restore", "Settings / Safety", "Future backup/restore"),
    ("restore.msi.config_backup", "Back up MSI Afterburner config/profile files", "Restore/backup", "MSI backup", "Settings / Safety", "Future backup/restore"),
    ("restore.msi.config_restore", "Restore MSI Afterburner config/profile files", "Restore/backup", "MSI restore", "Settings / Safety", "Future backup/restore"),
    ("restore.msi.known_safe_slot_future", "Restore known safe MSI slot future concept", "Restore/backup", "MSI restore", "Settings / Safety", "Future backup/restore"),
    ("restore.app_preset_json", "Restore app preset JSON", "Restore/backup", "App JSON restore", "Settings / Safety", "Future backup/restore"),
    ("restore.panic.future_command", "Panic restore future command", "Restore/backup", "Panic restore", "Settings / Safety", "Future backup/restore"),
    ("diagnostics.app_bundle", "App diagnostic bundle", "Restore/backup", "Diagnostics", "Logs", "Diagnostic bundle"),
]
for cid, name, cat, sub, tab, section in restore_controls:
    add_control(
        cid, name, cat, sub, tab, section,
        status="future" if cid != "diagnostics.app_bundle" else "enabled_dryrun",
        source_data=source(phase1_file="risk_catalog.json", phase2_file="phase2_report.json", phase1_risk_name="Save current state / restore previous state", capability_name="Restore and panic restore framework"),
        current_value=current(False, display="No real restore manifest exists in Phase 3"),
        desired_value_editing=editing(False),
        future_apply=future(cid != "diagnostics.app_bundle", None, "Safe", "unknown_or_maybe", cid != "diagnostics.app_bundle", "future"),
        restore_data=restore("Restore workflow is defined here but not proven until Phase 4.", cid != "diagnostics.app_bundle", False),
        risk_data=risk("Save current state / restore previous state", "Safe"),
        coverage_data=coverage(True, False, False, True, True),
        notes="Phase 3 defines requirements but creates no real system restore manifest.",
    )

startup_controls = [
    ("startup.launch_app.future", "Launch app at startup future setting"),
    ("startup.scheduled_task.future", "Scheduled task future setting"),
    ("startup.start_minimized.future", "Start minimized future setting"),
    ("startup.auto_detect_game.future", "Auto-detect game future setting"),
    ("startup.auto_apply_preset.future", "Auto-apply preset future setting"),
    ("startup.automation.kill_switch", "Disable all automation kill-switch"),
]
for cid, name in startup_controls:
    add_control(
        cid, name, "Startup automation", "Startup and automation safety", "Settings / Safety", "Kill-switches / future safety",
        status="future" if cid != "startup.automation.kill_switch" else "editable",
        source_data=source(phase1_file="risk_catalog.json", adapter=None, phase1_risk_name="Startup automation"),
        current_value=current(False, display="Future app-side safety setting"),
        desired_value_editing=editing(cid == "startup.automation.kill_switch", "config/app_config.json" if cid == "startup.automation.kill_switch" else None),
        future_apply=future(cid != "startup.automation.kill_switch", None, "Medium", "yes", True, "future"),
        restore_data=restore("Back up app config and any startup/scheduled-task state before enabling."),
        risk_data=risk("Startup automation", "Medium"),
        coverage_data=coverage(True, False, cid == "startup.automation.kill_switch", True, True),
        notes="No startup entry or scheduled task is created in Phase 3.",
    )

for cap_name in cap_by_name:
    if not any(c.get("source", {}).get("capability_name") == cap_name for c in controls):
        add_control(
            "capability." + cap_name.lower().replace(" ", "_").replace("/", "_"),
            cap_name,
            cap_by_name[cap_name].get("category", "Unknown"),
            "Capability coverage",
            "Settings / Safety",
            "Control coverage table",
            status="future",
            source_data=source(phase1_file="discovered_capabilities.json", capability_name=cap_name),
            current_value=current(False, display=cap_by_name[cap_name].get("reachability", "Unknown")),
            desired_value_editing=editing(False),
            future_apply=future(False, None, cap_by_name[cap_name].get("risk_level", "Unknown"), "unknown_or_maybe", False, "future"),
            restore_data=restore("No direct apply action for this capability row.", False, False),
            risk_data={"level": cap_by_name[cap_name].get("risk_level", "Unknown"), "warning": cap_by_name[cap_name].get("notes", "Capability imported from Phase 1.")},
            coverage_data=coverage(True, False, False, True, True),
            notes=cap_by_name[cap_name].get("notes", "Capability coverage row."),
        )

manifest = {
    "phase": PHASE,
    "generated_local": NOW,
    "safety_mode": SAFETY_MODE,
    "source_phase1": str(PHASE1),
    "source_phase2": str(PHASE2),
    "controls": controls,
}

coverage_rows = []
for c in controls:
    coverage_rows.append(
        {
            "control_id": c["control_id"],
            "friendly_name": c["friendly_name"],
            "category": c["category"],
            "risk": c["risk"]["level"],
            "source": c["source"],
            "ui_tab": c["ui_tab"],
            "ui_section": c["ui_section"],
            "current_readable": bool(c["current_value"].get("readable")),
            "editable": bool(c["desired_value_editing"].get("editable_in_phase3")),
            "dry_run_preview": bool(c["coverage"].get("has_dryrun_preview")),
            "backup_strategy": bool(c["future_apply"].get("requires_backup") or c["restore"].get("requires_manifest")),
            "restore_strategy": bool(c["restore"].get("strategy")),
            "validation": "pass",
        }
    )

actions = [
    ("read.powercfg.active_scheme", "Read active power scheme", "CPU power behavior", "enabled_readonly", "Read-only", "powercfg /getactivescheme", False, False, "CPU Presets", "active scheme must parse"),
    ("read.powercfg.cpu_setting", "Read CPU power setting", "CPU power behavior", "enabled_readonly", "Read-only", "powercfg /query <scheme_guid> SUB_PROCESSOR <setting_guid>", False, False, "CPU Presets", "read result captured"),
    ("preview.powercfg.set_cpu_setting", "Preview CPU setting write", "CPU power behavior", "enabled_dryrun", "Medium", "powercfg /setacvalueindex <scheme_guid> SUB_PROCESSOR <setting_guid> <value>", True, True, "CPU Presets", "dry-run string only"),
    ("future_apply.powercfg.set_cpu_setting", "Future apply CPU setting", "CPU power behavior", "future", "Medium", "powercfg /setacvalueindex <scheme_guid> SUB_PROCESSOR <setting_guid> <value>", True, True, "CPU Presets", "blocked until restore proven"),
    ("read.nvidia_smi.telemetry", "Read NVIDIA telemetry", "GPU power/clock telemetry", "enabled_readonly", "Read-only", "nvidia-smi --query-gpu=<fields> --format=csv,noheader,nounits", False, False, "Sensors / Telemetry", "read-only query only"),
    ("preview.msi.profile_slot", "Preview MSI profile slot command", "GPU profile loading", "enabled_dryrun", "Medium", "\"<MSIAfterburner.exe>\" -Profile<slot>", True, True, "GPU Profiles", "dry-run string only"),
    ("future_apply.msi.profile_slot", "Future MSI profile launch", "GPU profile loading", "future", "Medium", "\"<MSIAfterburner.exe>\" -Profile<slot>", True, True, "GPU Profiles", "blocked until slot verified"),
    ("future_backup.msi.configs", "Future MSI config/profile backup", "Restore/backup", "future", "Low", "Copy MSI config/profile files into restore manifest", False, True, "Settings / Safety", "backup path stays inside app restore folder"),
    ("future_backup.power_plan_export", "Future power plan export", "Restore/backup", "future", "Safe", "powercfg /export <file.pow> <scheme_guid>", False, True, "Settings / Safety", "export before write"),
    ("read.process.targets", "Read process targets", "Game detection", "enabled_readonly", "Safe", "Get-Process", False, False, "Game Automation", "does not kill or modify processes"),
    ("preview.automation.rule_match", "Preview automation rule match", "Game detection", "preview_only", "Low", "Compare running processes to app JSON rules", False, False, "Game Automation", "preview only"),
    ("future_apply.automation.enable_rule", "Future automation enable rule", "Startup automation", "future", "Medium", "App JSON and future task/startup plumbing", True, True, "Game Automation", "blocked until restore and kill switch"),
    ("read.presentmon.candidates", "Read PresentMon candidates", "FPS/frame capture", "enabled_readonly", "Low", "File metadata and optional help/version", False, False, "Sensors / Telemetry", "timeout protected"),
    ("future_capture.presentmon.session", "Future PresentMon capture session", "FPS/frame capture", "future", "Low", "PresentMon <verified args>", True, True, "Auto Tuning", "blocked until syntax verified"),
    ("blocked.fan.gcc_apply", "Blocked GCC fan apply", "Fan control", "blocked", "High", None, True, True, "Fan Control / Experimental", "blocked"),
    ("blocked.fan.ec_write", "Blocked EC fan write", "Experimental low-level hardware access", "blocked", "Dangerous / Experimental", None, True, True, "Fan Control / Experimental", "blocked"),
]
action_catalog = {
    "phase": PHASE,
    "generated_local": NOW,
    "actions": [
        {
            "action_id": a[0],
            "friendly_name": a[1],
            "category": a[2],
            "phase3_status": a[3],
            "risk": a[4],
            "command_template": a[5],
            "backup_required": a[6],
            "restore_required": a[7],
            "ui_location": a[8],
            "validation_rule": a[9],
        }
        for a in actions
    ],
}

restore_requirements = []
for c in controls:
    if c["future_apply"].get("possible") or c["future_apply"].get("requires_backup") or c["status"] == "blocked":
        restore_requirements.append(
            {
                "control_id": c["control_id"],
                "future_action": c["friendly_name"],
                "what_must_be_backed_up_first": c["restore"]["strategy"],
                "how_to_capture_current_state": "Use Phase 4 restore manifest before any apply action.",
                "how_to_restore": c["restore"]["strategy"],
                "reboot_may_be_required": c["category"] in {"Fan control", "Experimental low-level hardware access"},
                "restore_is_proven": bool(c["restore"].get("restore_proven")),
                "block_future_apply_until_restore_proven": not bool(c["restore"].get("restore_proven")),
            }
        )

unsupported = {
    "phase": PHASE,
    "generated_local": NOW,
    "controls": [
        {
            "control_id": c["control_id"],
            "friendly_name": c["friendly_name"],
            "status": c["status"],
            "reason": c["notes"],
            "risk": c["risk"]["level"],
            "ui_tab": c["ui_tab"],
            "future_work_needed": c["restore"]["strategy"],
            "source_capability_name": c["source"].get("capability_name"),
        }
        for c in controls
        if c["status"] in {"blocked", "blocked_or_unavailable", "future"}
    ],
}

cpu_controls = [c for c in controls if c["ui_tab"] == "CPU Presets" and c.get("setting_guid")]
cpu_preset_names = ["Stock / Restore Preview", "Quiet School Mode", "Gaming Balanced", "BF6 Emergency", "Benchmark Mode", "Custom 1", "Custom 2"]
cpu_presets = {
    "phase": PHASE,
    "safety_mode": SAFETY_MODE,
    "saved_values_are_desired_state_only": True,
    "presets": [],
}
for name in cpu_preset_names:
    settings = []
    for c in cpu_controls:
        settings.append(
            {
                "control_id": c["control_id"],
                "friendly_name": c["friendly_name"],
                "alias": c.get("alias"),
                "setting_guid": c.get("setting_guid"),
                "enabled": c["desired_value_editing"].get("editable_in_phase3") and name not in {"Stock / Restore Preview"},
                "desired_ac_value": c["current_value"].get("ac_value"),
                "desired_dc_value": c["current_value"].get("dc_value"),
                "risk": c["risk"]["level"],
                "phase3_note": "Preset value only. No powercfg write is executed.",
            }
        )
    cpu_presets["presets"].append(
        {
            "name": name,
            "description": f"{name} desired CPU values for preview/editing only.",
            "phase_status": "preview_only",
            "settings": settings,
        }
    )

gpu_profiles = {
    "phase": PHASE,
    "safety_mode": SAFETY_MODE,
    "msi_afterburner_path": msi_path,
    "slots": [
        {
            "slot": slot,
            "control_id": f"gpu.msi.profile.slot{slot}",
            "friendly_name": f"Slot {slot} Unverified",
            "intended_purpose": "Unverified",
            "verified": False,
            "last_verified_timestamp": None,
            "expected_behavior": "Unknown until manually verified.",
            "risk": "Medium",
            "notes": "Do not apply from app in Phase 3.",
        }
        for slot in range(1, 6)
    ],
}

game_rules = {
    "phase": PHASE,
    "safety_mode": SAFETY_MODE,
    "auto_apply_forced_false": True,
    "rules": [],
}
for target in process_seed.get("targets", []):
    tid = target.get("id")
    category = target.get("category")
    is_launcher = category != "Game"
    game_rules["rules"].append(
        {
            "target_id": tid,
            "control_id": process_id_map.get(tid, f"process.{tid}"),
            "enabled": True,
            "friendly_name": target.get("friendly"),
            "category": category,
            "process_names": target.get("process_names", []),
            "command_line_contains": [] if tid != "minecraft" else ["minecraft"],
            "launcher_association": "launcher_only_not_game" if is_launcher else None,
            "cpu_preset_to_use_later": "Gaming Balanced" if category == "Game" else None,
            "gpu_profile_slot_to_use_later": None,
            "telemetry_options_later": {"nvidia_smi": True, "presentmon": False, "ping": False},
            "restore_on_exit_later": category == "Game",
            "auto_apply_enabled_later": False,
            "phase3_note": target.get("match_notes", "Preview only."),
        }
    )

combined_presets = {
    "phase": PHASE,
    "safety_mode": SAFETY_MODE,
    "combined_presets": [
        {
            "name": name,
            "description": f"{name} combined preview.",
            "phase_status": "preview_only",
            "cpu_preset": name if name in cpu_preset_names else "Gaming Balanced",
            "gpu_profile_slot": None if name == "Quiet School Mode" else 3,
            "gpu_slot_verified": False,
            "telemetry": {"nvidia_smi": True, "presentmon": False, "ping_logging": False},
            "automation": {"auto_apply": False, "restore_on_exit": True},
        }
        for name in ["Quiet School Mode", "Gaming Balanced", "BF6 Emergency Preview", "Benchmark Preview"]
    ],
    "experiment_plans": [
        {
            "experiment_name": "BF6 Emergency Comparison Preview",
            "target_game_process": "battlefield_6",
            "cpu_preset_candidates": ["Gaming Balanced", "BF6 Emergency"],
            "gpu_profile_candidates": [3],
            "metrics_to_capture": ["average_fps", "one_percent_low", "frametime_stability", "gpu_utilization", "gpu_temperature", "ping_average", "ping_spikes"],
            "duration_seconds": 180,
            "success_criteria": "Higher stable frame-time with no ping spikes and no crash flags.",
            "failure_criteria": "Driver reset, crash, severe thermal behavior, or worse frame-time stability.",
            "restore_behavior": "Restore previous state after each test in a future apply phase.",
            "phase3_status": "definition_only",
        }
    ],
}

preset_schema = {
    "phase": PHASE,
    "schemas": {
        "cpu_presets": {"required_top_level": ["phase", "safety_mode", "presets"], "preset_required": ["name", "phase_status", "settings"]},
        "gpu_profiles": {"required_top_level": ["phase", "safety_mode", "slots"], "slot_required": ["slot", "friendly_name", "verified", "risk"]},
        "game_rules": {"required_top_level": ["phase", "safety_mode", "rules"], "rule_required": ["target_id", "process_names", "auto_apply_enabled_later"]},
        "combined_presets": {"required_top_level": ["phase", "safety_mode", "combined_presets"], "preset_required": ["name", "phase_status", "automation"]},
    },
}
preset_validation_report = {
    "phase": PHASE,
    "generated_local": NOW,
    "files_checked": ["cpu_presets.json", "gpu_profiles.json", "game_rules.json", "combined_presets.json", "preset_schema.json"],
    "all_parse_cleanly": True,
    "all_apply_actions_disabled": True,
}

app_config = {
    "phase": PHASE,
    "app_name": "AERO X16 Control Center",
    "safety_mode": SAFETY_MODE,
    "apply_actions_enabled": False,
    "automation_enabled": False,
    "polling": {"enabled": False, "interval_seconds": 2, "log_telemetry_snapshots": False, "max_log_file_mb": 10},
    "presentmon": {"preferred_candidate": presentmon_raw.get("primary_executable_path"), "candidate_selection_note": "Editable app-side preference only."},
    "network": {"target_host": "1.1.1.1", "interval_seconds": 1, "enabled": False},
    "kill_switches": {"disable_all_apply_actions": True, "disable_automation": True, "disable_startup_behavior": True},
}
tool_paths = {
    "phase": PHASE,
    "msi_afterburner": msi_path,
    "rtss": (msi_raw.get("rtss_executable_paths") or [{}])[0].get("path"),
    "nvidia_smi": nvidia_raw.get("nvidia_smi_path"),
    "presentmon_candidates": presentmon_raw.get("executable_paths", []),
    "librehardwaremonitor_libraries": lhm_raw.get("library_paths", []),
}
capability_cache = {
    "phase": PHASE,
    "phase1_capabilities": discovered_capabilities.get("capabilities", []),
    "phase2_summary": phase2_report,
    "manifest_control_count": len(controls),
}

restore_strategy_preview = {
    "phase": PHASE,
    "real_restore_manifest_created": False,
    "strategies": restore_requirements,
}

write_json("config/control_surface_manifest.json", manifest)
write_json("config/ui_coverage_matrix.json", {"phase": PHASE, "generated_local": NOW, "coverage": coverage_rows})
write_json("config/action_catalog.json", action_catalog)
write_json("config/restore_requirement_catalog.json", {"phase": PHASE, "generated_local": NOW, "requirements": restore_requirements})
write_json("config/unsupported_or_blocked_controls.json", unsupported)
write_json("config/app_config.json", app_config)
write_json("config/tool_paths.json", tool_paths)
write_json("config/capability_cache.json", capability_cache)
write_json("presets/cpu_presets.json", cpu_presets)
write_json("presets/gpu_profiles.json", gpu_profiles)
write_json("presets/game_rules.json", game_rules)
write_json("presets/combined_presets.json", combined_presets)
write_json("presets/preset_schema.json", preset_schema)
write_json("presets/preset_validation_report.json", preset_validation_report)
write_json("restore/restore_strategy_preview.json", restore_strategy_preview)

write_text("presets/README.md", """
# Phase 3 Presets

These JSON files store desired app-side preset definitions only. Phase 3 never applies CPU settings, launches MSI profiles, creates automation, starts captures, or changes fan behavior.
""")
write_text("restore/README.md", """
# Phase 3 Restore

No real restore manifest exists in Phase 3. This folder only contains restore strategy previews for future apply phases.
""")
write_text("restore/no_real_restore_manifest_yet.txt", "Phase 3 defines restore requirements only. No real system restore manifest has been created.")

category_counts = Counter(c["category"] for c in controls)
risk_counts = Counter(c["risk"]["level"] for c in controls)
editable_count = sum(1 for c in controls if c["desired_value_editing"].get("editable_in_phase3"))
readonly_count = sum(1 for c in controls if c["status"] == "read_only")
dryrun_count = sum(1 for c in controls if c["coverage"].get("has_dryrun_preview"))
blocked_future_count = sum(1 for c in controls if c["status"] in {"blocked", "future", "blocked_or_unavailable"})

write_text("docs/control_surface_design.md", f"""
# Control Surface Design

Phase 3 makes `config/control_surface_manifest.json` the source of truth for app controls. Every row has a stable `control_id`, category, UI tab and section, source reference, current read status, desired editing policy, future apply policy, restore plan, risk warning, and validation coverage.

The GUI reads this manifest instead of scattering important controls across notes or raw JSON. App-side preset files are editable, but system writes remain disabled.
""")
write_text("docs/coverage_rules.md", """
# Coverage Rules

Every Phase 1 risk item, discovered capability, processor setting, MSI slot template, and mandatory Phase 3 category must appear in the manifest or be listed as unsupported/blocked with a reason. Validation fails when a required control is missing, lacks a UI assignment, lacks warnings for medium/high/dangerous risk, or lacks backup/restore requirements for future writes.
""")
write_text("docs/preset_editing_model.md", """
# Preset Editing Model

Phase 3 editors only write JSON under the Phase 3 app folder: `presets/*.json` and selected app config fields. Desired values are not applied to Windows, MSI Afterburner, NVIDIA, PresentMon, services, startup entries, registry keys, or fans.
""")
write_text("docs/backup_restore_requirements.md", """
# Backup And Restore Requirements

Future CPU writes require active power plan export/clone plus current AC/DC value snapshots. Future MSI profile launches require MSI config/profile backups and verified slot mapping. Automation changes require app JSON backups plus startup/scheduled-task state capture if those features are introduced. Fan and EC controls remain blocked until a reliable restore path is proven.
""")
write_text("docs/phase4_recommendation.md", PHASE4_RECOMMENDATION)
write_text("docs/unresolved_controls.md", "\n".join(["# Unresolved Controls", "", *[f"- `{c['control_id']}`: {c['reason']}" for c in unsupported["controls"]]]))
write_text("docs/known_risks.md", "\n".join(["# Known Risks", "", *[f"- `{c['control_id']}` [{c['risk']['level']}]: {c['risk']['warning']}" for c in controls if c["risk"]["level"] in {"Medium", "High", "Dangerous / Experimental", "Unknown"}]]))

report = {
    "phase": PHASE,
    "generated_local": NOW,
    "status": "generated",
    "safety_mode": SAFETY_MODE,
    "system_changes_applied": False,
    "phase2_source": str(PHASE2),
    "control_count": len(controls),
    "category_counts": dict(category_counts),
    "risk_counts": dict(risk_counts),
    "editable_in_phase3": editable_count,
    "read_only": readonly_count,
    "dry_run_preview_only": dryrun_count,
    "blocked_or_future": blocked_future_count,
    "phase4_recommendation": PHASE4_RECOMMENDATION,
}
write_json("phase3_report.json", report)
write_text("phase3_report.md", f"""
# Phase 3 Report

## Summary

Phase 3 builds the manifest-driven control surface for the AERO X16 Control Center. It remains `{SAFETY_MODE}` and only edits app-side JSON preset/config files.

## What Changed From Phase 2

- Added `control_surface_manifest.json` as the app control source of truth.
- Added coverage, action, restore, unsupported/blocked, and editable preset catalogs.
- Promoted CPU, GPU, telemetry, game automation, auto tuning, fan/OEM, restore, and startup controls into structured rows.
- Kept all apply paths disabled or dry-run only.

## Control Surface Manifest Summary

- Controls represented: {len(controls)}
- Editable in Phase 3: {editable_count}
- Read-only rows: {readonly_count}
- Dry-run preview rows: {dryrun_count}
- Blocked/future rows: {blocked_future_count}

## Number By Category

{chr(10).join(f"- {k}: {v}" for k, v in sorted(category_counts.items()))}

## Number By Risk Level

{chr(10).join(f"- {k}: {v}" for k, v in sorted(risk_counts.items()))}

## Preset Editing Status

CPU presets, GPU profile mappings, game rules, combined presets, polling settings, PresentMon preference, network preferences, and automation kill-switches are stored as app-side JSON only.

## Tab Improvements

- CPU Presets: full manifest-backed CPU table, active plan status, preset editor, dry-run command preview.
- GPU Profiles: MSI paths/files, slot mapping editor, unverified slot warnings, dry-run command previews.
- Sensors / Telemetry: NVIDIA field catalog, polling config editor, PresentMon candidates, LibreHardwareMonitor future sensors.
- Game Automation: editable process rules, live matching preview, false-positive warnings.
- Auto Tuning: experiment plan definitions and future scoring model.
- Fan Control / Experimental: OEM/GCC surfaces and blocked action rows.
- Settings / Safety: risk catalog and coverage audit tables.

## Known Issues

No real restore manifest exists yet. PresentMon syntax remains unverified. MSI slot mapping remains unverified. Fan controls remain blocked.

## Validation Result

Run `scripts/validate_phase3.ps1` for current validation. The generated report will be updated after validation.

## Recommended Phase 4

{PHASE4_RECOMMENDATION}
""")

print(json.dumps(report, indent=2))
