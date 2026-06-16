from __future__ import annotations

from collections import defaultdict
from typing import Any


class SensorPresentation:
    """Build Phase 8 display models from normalized telemetry.

    The normalizer decides what a sensor means. This layer decides how that
    telemetry should be presented in the UI without changing selection logic.
    """

    def __init__(self, model: dict[str, Any], history: Any | None = None, polling_active: bool = False) -> None:
        self.model = model or {}
        self.headline = self.model.get("headline", {}) or {}
        self.sources = self.model.get("sources", {}) or {}
        self.raw_sensors = self.model.get("raw_sensors", []) or []
        self.groups = self.model.get("groups", {}) or {}
        self.diagnostics = self.model.get("diagnostics", {}) or {}
        self.history = history
        self.polling_active = polling_active

    def build(self) -> dict[str, Any]:
        return {
            "hero_cards": self._hero_cards(),
            "status_pills": self._status_pills(),
            "hardware_panels": self._hardware_panels(),
            "favorite_cards": self._favorite_cards(),
            "diagnostics": self._diagnostics(),
            "raw_table_rows": self._raw_table_rows(),
        }

    def _hero_cards(self) -> list[dict[str, Any]]:
        return [
            self.with_history(self._cpu_hero()),
            self.with_history(self._gpu_hero()),
            self.with_history(self._memory_hero()),
            self.with_history(self._frame_hero()),
        ]

    def _cpu_hero(self) -> dict[str, Any]:
        temp = self._number(self.headline.get("cpu_temp_c"))
        load = self._number(self.headline.get("cpu_load_percent"))
        power = self._number(self.headline.get("cpu_power_w"))
        clock = self._number(self.headline.get("cpu_clock_mhz"))
        voltage = self._number(self.headline.get("cpu_voltage_v"))
        diag = self._diagnostics().get("cpu_temperature", {})
        if temp is not None:
            primary = temp
            value_display = self._compact_number(temp)
            unit = "C"
            subtitle = self.headline.get("cpu_temp_name") or "CPU temperature"
            tone = self._temp_tone(temp)
            progress = load
            history_key = "cpu_temp_c"
        elif load is not None:
            primary = load
            value_display = f"{load:.0f}"
            unit = "%"
            subtitle = "CPU load"
            tone = "warn" if diag.get("warning") else "normal"
            progress = load
            history_key = "cpu_load_percent"
        elif voltage is not None:
            primary = voltage
            value_display = self._format_voltage(voltage)
            unit = "V"
            subtitle = "CPU voltage"
            tone = "warn"
            progress = None
            history_key = None
        else:
            primary = None
            value_display = "unavailable"
            unit = ""
            subtitle = diag.get("warning") or "CPU telemetry unavailable"
            tone = "unavailable"
            progress = None
            history_key = None
        return {
            "key": "cpu",
            "title": "CPU Load" if temp is None and load is not None else "CPU",
            "value": primary,
            "value_display": value_display,
            "unit": unit,
            "subtitle": self._dedupe_subtitle(value_display, subtitle),
            "source": "LHM",
            "tone": tone,
            "progress": progress,
            "history_key": history_key,
            "chips": self._cpu_chips(temp, load, power, clock, voltage, diag),
        }

    def _gpu_hero(self) -> dict[str, Any]:
        temp = self._number(self.headline.get("gpu_temp_c"))
        util = self._number(self.headline.get("gpu_util_percent"))
        power = self._number(self.headline.get("gpu_power_w"))
        clock = self._number(self.headline.get("gpu_clock_mhz"))
        gpu_name = self._first_gpu_name()
        return {
            "key": "gpu",
            "title": "GPU",
            "value": temp,
            "value_display": self._compact_number(temp) if temp is not None else "unavailable",
            "unit": "C" if temp is not None else "",
            "subtitle": gpu_name or "nvidia-smi telemetry",
            "source": "nvidia-smi",
            "tone": self._temp_tone(temp),
            "progress": util,
            "history_key": "gpu_temp_c" if temp is not None else "gpu_util_percent",
            "chips": self._chips(
                [
                    ("Load", util, "%", None),
                    ("Power", power, "W", 1),
                    ("Clock", clock, "MHz", 0),
                ]
            ),
        }

    def _memory_hero(self) -> dict[str, Any]:
        ram_load = self._number(self.headline.get("ram_load_percent"))
        vram_used = self._number(self.headline.get("vram_used_mb"))
        vram_total = self._number(self.headline.get("vram_total_mb"))
        if vram_used is not None and vram_total:
            value_display = f"{vram_used:.0f} / {vram_total:.0f}"
            unit = "MB"
            progress = (vram_used / vram_total) * 100
            subtitle = "VRAM used / total"
        elif ram_load is not None:
            value_display = self._compact_number(ram_load)
            unit = "%"
            progress = ram_load
            subtitle = "System RAM load"
        else:
            value_display = "unavailable"
            unit = ""
            progress = None
            subtitle = "Memory telemetry unavailable"
        return {
            "key": "memory",
            "title": "Memory / VRAM",
            "value": vram_used if vram_used is not None else ram_load,
            "value_display": value_display,
            "unit": unit,
            "subtitle": subtitle,
            "source": "mixed",
            "tone": self._percent_tone(progress),
            "progress": progress,
            "history_key": "vram_used_mb" if vram_used is not None else "ram_load_percent",
            "chips": self._chips(
                [
                    ("RAM", ram_load, "%", None),
                    ("VRAM", vram_used, "MB", 0),
                    ("Total", vram_total, "MB", 0),
                ]
            ),
        }

    def _frame_hero(self) -> dict[str, Any]:
        fps = self._number(self.headline.get("fps"))
        frame_time = self._number(self.headline.get("frame_time_ms"))
        presentmon = self.sources.get("presentmon", {}) or {}
        source_status = str(presentmon.get("status") or ("ok" if presentmon.get("ok") else "idle"))
        value_display = self._compact_number(fps) if fps is not None else "idle"
        subtitle = self._presentmon_subtitle()
        return {
            "key": "frames",
            "title": "Frames",
            "value": fps,
            "value_display": value_display,
            "unit": "FPS" if fps is not None else "",
            "subtitle": subtitle,
            "source": "PresentMon",
            "tone": "normal" if fps is not None else "unavailable",
            "progress": None,
            "history_key": "fps" if fps is not None else "frame_time_ms",
            "chips": self._chips(
                [
                    ("Frame time", frame_time, "ms", 2),
                    ("State", source_status, "", None),
                ]
            ),
        }

    def _status_pills(self) -> list[dict[str, Any]]:
        return [
            self._source_pill("LHM", "lhm"),
            self._source_pill("NVIDIA", "nvidia_smi"),
            {"label": "CPU provider", "value": str(self.headline.get("cpu_provider_health") or "unknown"), "tone": self._provider_tone(str(self.headline.get("cpu_provider_health") or ""))},
            self._source_pill("PresentMon", "presentmon", idle_label="idle"),
            {"label": "Raw sensors", "value": str(len(self.raw_sensors)), "tone": "normal"},
            {"label": "Last refresh", "value": self.model.get("generated_local") or "not read", "tone": "neutral"},
            {"label": "Polling", "value": "live" if self.polling_active else "paused", "tone": "safe" if self.polling_active else "neutral"},
        ]

    def _source_pill(self, label: str, source_key: str, idle_label: str = "unavailable") -> dict[str, Any]:
        source = self.sources.get(source_key, {}) or {}
        if source.get("ok"):
            value = str(source.get("status") or "ok")
            tone = "safe"
        else:
            value = str(source.get("status") or idle_label)
            tone = "unavailable"
        return {"label": label, "value": value, "tone": tone}

    def _hardware_panels(self) -> list[dict[str, Any]]:
        return [
            self.with_history(self._cpu_panel()),
            self.with_history(self._gpu_panel()),
            self.with_history(self._memory_panel()),
            self.with_history(self._fans_panel()),
            self.with_history(self._storage_panel()),
            self.with_history(self._power_panel()),
            self.with_history(self._frame_panel()),
            self.with_history(self._other_panel()),
        ]

    def _cpu_panel(self) -> dict[str, Any]:
        diag = self._diagnostics().get("cpu_temperature", {})
        cpu_rows = self.groups.get("cpu", [])
        valid_rows = [row for row in cpu_rows if row.get("validity") == "valid"]
        stale_rows = [row for row in cpu_rows if row.get("validity") == "stale_zero"]
        return {
            "key": "cpu",
            "title": "CPU",
            "subtitle": diag.get("provider_summary") or diag.get("summary") or "Processor telemetry from LibreHardwareMonitor.",
            "tone": self._temp_tone(self._number(self.headline.get("cpu_temp_c"))),
            "history_key": "cpu_temp_c",
            "metrics": self._chips(
                [
                    ("Temp", self.headline.get("cpu_temp_c"), "C", 0),
                    ("Load", self.headline.get("cpu_load_percent"), "%", None),
                    ("Power", self.headline.get("cpu_power_w"), "W", 1),
                    ("Clock", self.headline.get("cpu_clock_mhz"), "MHz", 0),
                    ("Voltage", self.headline.get("cpu_voltage_v"), "V", 2),
                ]
            )
            + self._status_chips([("Temp", self.headline.get("cpu_temp_c")), ("Power", self.headline.get("cpu_power_w")), ("Clock", self.headline.get("cpu_clock_mhz"))]),
            "details_title": "Available CPU metrics and stale-zero readings",
            "details": self._detail_rows(valid_rows + stale_rows, 8),
            "empty_text": diag.get("warning") or "No CPU sensors available yet.",
        }

    def _gpu_panel(self) -> dict[str, Any]:
        return {
            "key": "gpu",
            "title": "GPU",
            "subtitle": self._first_gpu_name() or "NVIDIA and LHM GPU telemetry.",
            "tone": self._temp_tone(self._number(self.headline.get("gpu_temp_c"))),
            "history_key": "gpu_temp_c",
            "metrics": self._chips(
                [
                    ("Temp", self.headline.get("gpu_temp_c"), "C", 0),
                    ("Load", self.headline.get("gpu_util_percent"), "%", None),
                    ("Power", self.headline.get("gpu_power_w"), "W", 1),
                    ("Clock", self.headline.get("gpu_clock_mhz"), "MHz", 0),
                    ("VRAM", self.headline.get("vram_used_mb"), "MB", 0),
                ]
            ),
            "details_title": "GPU detail sensors",
            "details": self._detail_rows(self.groups.get("gpu", []), 8),
            "empty_text": "GPU telemetry unavailable.",
        }

    def _memory_panel(self) -> dict[str, Any]:
        return {
            "key": "memory",
            "title": "Memory / VRAM",
            "subtitle": self.headline.get("vram_status_display") or "RAM and VRAM utilization.",
            "tone": self._percent_tone(self._number(self.headline.get("ram_load_percent"))),
            "history_key": "ram_load_percent",
            "metrics": self._chips(
                [
                    ("RAM load", self.headline.get("ram_load_percent"), "%", None),
                    ("VRAM used", self.headline.get("vram_used_mb"), "MB", 0),
                    ("VRAM total", self.headline.get("vram_total_mb"), "MB", 0),
                ]
            ),
            "details_title": "Memory sensors",
            "details": self._detail_rows(self.groups.get("memory", []), 8),
            "empty_text": "Memory sensors not exposed yet.",
        }

    def _fans_panel(self) -> dict[str, Any]:
        fan = self._number(self.headline.get("fan_rpm"))
        return {
            "key": "fans",
            "title": "Fans / Cooling",
            "subtitle": "Fan RPM not exposed by laptop firmware/LHM." if fan is None else "Cooling telemetry exposed by LHM.",
            "tone": "unavailable" if fan is None else "safe",
            "history_key": "fan_rpm",
            "metrics": self._chips([("Fan", fan, "RPM", 0)]),
            "details_title": "Fan sensors",
            "details": self._detail_rows(self.groups.get("fans", []), 8),
            "empty_text": "Fan RPM not exposed by laptop firmware/LHM.",
        }

    def _storage_panel(self) -> dict[str, Any]:
        storage_rows = self.groups.get("storage", [])
        hottest = max((self._number(row.get("value")) for row in storage_rows if row.get("sensor_type") == "Temperature"), default=None)
        return {
            "key": "storage",
            "title": "Storage",
            "subtitle": "SSD/NVMe temperatures and activity sensors when exposed.",
            "tone": self._temp_tone(hottest),
            "history_key": "storage_temperature_c",
            "metrics": self._chips([("Hottest", hottest, "C", 0), ("Sensors", len(storage_rows), "", None)]),
            "details_title": "Storage sensors",
            "details": self._detail_rows(storage_rows, 8),
            "empty_text": "No storage sensors exposed.",
        }

    def _power_panel(self) -> dict[str, Any]:
        rows = (self.groups.get("battery_power", []) or []) + (self.groups.get("motherboard", []) or [])
        return {
            "key": "power",
            "title": "Power / Battery",
            "subtitle": "Battery, AC adapter, motherboard, and controller sensors.",
            "tone": "normal" if rows else "unavailable",
            "history_key": None,
            "metrics": self._chips([("Sensors", len(rows), "", None)]),
            "details_title": "Power and board sensors",
            "details": self._detail_rows(rows, 8),
            "empty_text": "No battery or board sensors exposed.",
        }

    def _frame_panel(self) -> dict[str, Any]:
        return {
            "key": "frames",
            "title": "Frame / PresentMon",
            "subtitle": self._presentmon_subtitle(),
            "tone": "normal" if self._number(self.headline.get("fps")) is not None else "unavailable",
            "history_key": "fps",
            "metrics": self._chips(
                [
                    ("FPS", self.headline.get("fps"), "FPS", 0),
                    ("Frame time", self.headline.get("frame_time_ms"), "ms", 2),
                ]
            ),
            "details_title": "Frame capture sensors",
            "details": self._detail_rows(self.groups.get("frames", []), 8),
            "empty_text": "PresentMon idle. Capture must be started manually.",
        }

    def _other_panel(self) -> dict[str, Any]:
        rows = (self.groups.get("network", []) or []) + (self.groups.get("other", []) or [])
        return {
            "key": "other",
            "title": "Network / Other",
            "subtitle": "Everything classified outside the primary hardware groups.",
            "tone": "normal" if rows else "unavailable",
            "history_key": None,
            "metrics": self._chips([("Sensors", len(rows), "", None)]),
            "details_title": "Other sensors",
            "details": self._detail_rows(rows, 10),
            "empty_text": "No network or miscellaneous sensors exposed.",
        }

    def _favorite_cards(self) -> list[dict[str, Any]]:
        favorites = [row for row in self.raw_sensors if row.get("favorite")]
        cards = []
        for row in favorites:
            cards.append(
                {
                    "source": row.get("source"),
                    "title": row.get("display_name") or row.get("name"),
                    "value_display": row.get("display_value") or "unavailable",
                    "subtitle": row.get("hardware"),
                    "tone": "normal",
                    "favorite_key": self._favorite_identity(row),
                }
            )
        return cards

    def _diagnostics(self) -> dict[str, Any]:
        cpu = dict(self.diagnostics.get("cpu_temperature", {}) or {})
        provider = dict(self.diagnostics.get("cpu_provider", {}) or {})
        selected = cpu.get("selected")
        if selected:
            cpu["summary"] = f"Selected {selected.get('name')} from {selected.get('hardware')} at {selected.get('value')} C."
            cpu["warning"] = ""
        else:
            rejected = cpu.get("rejected_candidates", []) or []
            invalid = [row for row in rejected if "invalid temperature" in str(row.get("reason", "")).lower()]
            if invalid:
                row = invalid[0]
                cpu["warning"] = (
                    f"CPU temperature unavailable because {row.get('name') or 'a CPU-like candidate'} "
                    f"reported {row.get('value')} C, which was rejected as invalid."
                )
            else:
                cpu["warning"] = cpu.get("failure_reason") or "CPU temperature unavailable."
            cpu["summary"] = cpu["warning"]
        cpu_rows = [row for row in self.raw_sensors if row.get("category") == "cpu"]
        cpu["raw_cpu_sensors"] = cpu_rows
        cpu["valid_cpu_sensors"] = [row for row in cpu_rows if row.get("validity") == "valid"]
        cpu["stale_zero_cpu_sensors"] = [row for row in cpu_rows if row.get("validity") == "stale_zero"]
        cpu["invalid_cpu_sensors"] = [row for row in cpu_rows if row.get("validity") == "invalid_value"]
        cpu["provider_summary"] = (
            "CPU telemetry is partial. LibreHardwareMonitor exposes CPU load and voltage, "
            "but CPU temperature returned 0 C, and CPU power/clock returned 0 values. "
            "These are marked unavailable/stale instead of shown as real metrics."
            if provider.get("status") == "partial"
            else provider.get("summary", "CPU provider status unavailable.")
        )
        cpu["provider_recommendation"] = (
            "Try alternate provider: HWiNFO shared memory if available. Try multi-sample "
            "LHM refresh before declaring unavailable."
        )
        cpu["metric_health"] = self._metric_health(cpu_rows)
        grouped = defaultdict(list)
        for row in cpu.get("rejected_candidates", []) or []:
            reason = str(row.get("reason") or "unknown")
            if "invalid temperature" in reason.lower():
                key = "invalid temperature"
            elif "not CPU-like" in reason:
                key = "not CPU-like"
            elif "missing numeric" in reason.lower():
                key = "missing numeric value"
            else:
                key = reason
            grouped[key].append(row)
        cpu["rejected_by_reason"] = dict(grouped)
        return {"cpu_temperature": cpu}

    def _raw_table_rows(self) -> list[dict[str, Any]]:
        rows = []
        for row in self.raw_sensors:
            selected = ", ".join(row.get("selected_for", []) or [])
            if row.get("selected_for_headline") and not selected:
                selected = "headline"
            rows.append(
                {
                    "favorite": "yes" if row.get("favorite") else "",
                    "selected": selected,
                    "category": row.get("category"),
                    "subcategory": row.get("subcategory"),
                    "hardware": row.get("hardware"),
                    "sensor_type": row.get("sensor_type"),
                    "name": row.get("name"),
                    "value": row.get("display_value"),
                    "unit": row.get("unit"),
                    "validity": row.get("validity"),
                    "validity_reason": row.get("validity_reason"),
                    "provider": row.get("provider"),
                    "notes": row.get("notes"),
                    "source": row.get("source"),
                    "hardware_type": row.get("hardware_type"),
                    "min": row.get("min"),
                    "max": row.get("max"),
                    "key": row.get("normalized_key"),
                    "score": row.get("score"),
                    "raw": row,
                }
            )
        return rows

    def _top_rows(self, category: str, sensor_type: str, limit: int) -> list[dict[str, Any]]:
        rows = [
            row
            for row in self.groups.get(category, [])
            if str(row.get("sensor_type", "")).lower() == sensor_type.lower()
        ]
        rows.sort(key=lambda row: (0 if row.get("selected_for_headline") else 1, -(self._number(row.get("value")) or 0)))
        return rows[:limit]

    def _detail_rows(self, rows: list[dict[str, Any]], limit: int) -> list[dict[str, str]]:
        return [
            {
                "name": str(row.get("name") or row.get("display_name") or "sensor"),
                "value": str(row.get("display_value") or "unavailable"),
                "source": str(row.get("source") or ""),
                "notes": str(row.get("validity_reason") or row.get("notes") or ""),
            }
            for row in rows[:limit]
        ]

    def _chips(self, specs: list[tuple[str, Any, str, int | None]]) -> list[dict[str, str]]:
        chips = []
        for label, value, unit, decimals in specs:
            if value is None or value == "":
                continue
            if isinstance(value, str):
                display = value
            else:
                number = self._number(value)
                if number is None:
                    display = str(value)
                elif decimals is None:
                    display = f"{number:.0f}{unit}" if unit in ("%",) else f"{number:.0f} {unit}".strip()
                elif decimals == 0:
                    display = f"{number:.0f} {unit}".strip()
                else:
                    display = f"{number:.{decimals}f} {unit}".strip()
            chips.append({"label": label, "value": display})
        return chips

    def _first_gpu_name(self) -> str:
        for row in self.raw_sensors:
            if row.get("category") == "gpu" and row.get("source") == "nvidia-smi" and row.get("hardware"):
                return str(row.get("hardware"))
        for row in self.raw_sensors:
            if row.get("category") == "gpu" and row.get("subcategory") == "dgpu" and row.get("hardware"):
                return str(row.get("hardware"))
        for row in self.raw_sensors:
            if row.get("category") == "gpu" and row.get("hardware"):
                return str(row.get("hardware"))
        return ""

    def _presentmon_subtitle(self) -> str:
        source = self.sources.get("presentmon", {}) or {}
        if source.get("ok"):
            return "PresentMon sample available"
        status = source.get("status") or "idle"
        if str(status).lower() in ("idle", "no data"):
            return "Start capture for FPS/frame-time"
        return f"PresentMon {status}"

    def _history_values(self, key: str | None) -> list[float]:
        if not key:
            return []
        if isinstance(self.history, dict):
            values = self.history.get(key, [])
            return [item.get("value", item) if isinstance(item, dict) else item for item in values]
        if hasattr(self.history, "values"):
            return list(self.history.values(key))
        return []

    def with_history(self, data: dict[str, Any]) -> dict[str, Any]:
        result = dict(data)
        result["history_values"] = self._history_values(result.get("history_key"))
        return result

    def _favorite_identity(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": row.get("source"),
            "hardware": row.get("hardware"),
            "sensor_type": row.get("sensor_type"),
            "name": row.get("name"),
        }

    def _number(self, value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _compact_number(self, value: float | None) -> str:
        if value is None:
            return "unavailable"
        return f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}"

    def _temp_tone(self, value: float | None) -> str:
        if value is None:
            return "unavailable"
        if value >= 95:
            return "danger"
        if value >= 85:
            return "warn"
        return "safe"

    def _percent_tone(self, value: float | None) -> str:
        if value is None:
            return "unavailable"
        if value >= 95:
            return "danger"
        if value >= 85:
            return "warn"
        return "normal"

    def _dedupe_subtitle(self, value_display: str, subtitle: str) -> str:
        if not subtitle:
            return ""
        if str(value_display).strip().lower() == str(subtitle).strip().lower():
            return ""
        return subtitle

    def _cpu_chips(self, temp: float | None, load: float | None, power: float | None, clock: float | None, voltage: float | None, diag: dict[str, Any]) -> list[dict[str, str]]:
        chips: list[dict[str, str]] = []
        if temp is None:
            chips.append({"label": "Temp", "value": "unavailable"})
        if load is not None:
            chips.extend(self._chips([("Load", load, "%", None)]))
        if power is None:
            chips.append({"label": "Power", "value": "unavailable"})
        else:
            chips.extend(self._chips([("Power", power, "W", 1)]))
        if clock is None:
            chips.append({"label": "Clock", "value": "unavailable"})
        else:
            chips.extend(self._chips([("Clock", clock, "MHz", 0)]))
        if voltage is not None:
            chips.append({"label": "VID", "value": self._format_voltage(voltage)})
        return chips

    def _status_chips(self, specs: list[tuple[str, Any]]) -> list[dict[str, str]]:
        chips = []
        for label, value in specs:
            if value is None:
                chips.append({"label": label, "value": "unavailable"})
        return chips

    def _format_voltage(self, value: float) -> str:
        return f"{value:.2f} V"

    def _provider_tone(self, status: str) -> str:
        lowered = status.lower()
        if lowered == "ok":
            return "safe"
        if lowered == "partial":
            return "warn"
        return "unavailable"

    def _metric_health(self, cpu_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        mapping = {
            "load": ("Load", None),
            "temperature": ("Temperature", None),
            "power": ("Power", None),
            "clock": ("Clock", None),
            "voltage": ("Voltage", None),
        }
        health: dict[str, dict[str, Any]] = {}
        for key, (sensor_type, _unused) in mapping.items():
            rows = [row for row in cpu_rows if str(row.get("sensor_type", "")).lower() == sensor_type.lower()]
            selected = next((row for row in rows if row.get("validity") == "valid"), rows[0] if rows else None)
            health[key] = {
                "validity": selected.get("validity") if selected else "unavailable",
                "value": selected.get("value") if selected else None,
                "name": selected.get("name") if selected else None,
                "reason": selected.get("validity_reason") if selected else "No sensor exposed.",
            }
        return health
