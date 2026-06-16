from __future__ import annotations

from datetime import datetime
from typing import Any


class SensorNormalizer:
    """Convert raw telemetry into a safe, source-aware display model.

    Phase 8 adds explicit validity states so provider artifacts such as CPU
    power at 0 W or clocks at 0 MHz are diagnosed instead of displayed as real
    laptop behavior.
    """

    CPU_TEMP_PRIORITY = [
        ("cpu package", 0, "preferred CPU package temperature"),
        ("package", 1, "preferred package temperature"),
        ("cpu core max", 2, "preferred CPU core max temperature"),
        ("core max", 3, "preferred core max temperature"),
        ("tctl/tdie", 4, "preferred AMD control/die temperature"),
        ("tdie", 5, "preferred die temperature"),
        ("tctl", 6, "preferred control temperature"),
        ("cpu die", 7, "preferred die temperature"),
        ("average cpu temp", 8, "preferred average CPU temperature"),
        ("core average", 9, "preferred core average temperature"),
        ("cpu ia cores", 10, "CPU IA cores temperature"),
        ("cpu gt cores", 11, "CPU GT cores temperature"),
        ("p-core max", 12, "P-core max temperature"),
        ("e-core max", 13, "E-core max temperature"),
        ("max", 20, "generic max CPU temperature"),
        ("average", 30, "generic average CPU temperature"),
        ("cpu", 40, "generic CPU temperature"),
        ("core", 50, "generic core temperature"),
    ]

    CPU_TERMS = ("cpu", "processor", "package", "core", "tctl", "tdie", "p-core", "e-core", "ia cores", "gt cores")
    VALIDITY_ORDER = ("valid", "unavailable", "stale_zero", "invalid_value", "unsupported", "hidden_by_firmware", "no_provider", "idle_no_capture", "not_started", "read_error")

    def normalize(
        self,
        lhm_snapshot: dict[str, Any] | None = None,
        nvidia_snapshot: dict[str, Any] | None = None,
        presentmon_snapshot: dict[str, Any] | None = None,
        favorites: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        favorite_keys = self._favorite_keys(favorites or {})
        sources = {
            "lhm": self._source_status("lhm", lhm_snapshot),
            "nvidia_smi": self._source_status("nvidia_smi", nvidia_snapshot),
            "presentmon": self._source_status("presentmon", presentmon_snapshot),
        }
        raw_sensors: list[dict[str, Any]] = []
        raw_sensors.extend(self._normalize_lhm_sensors(lhm_snapshot or {}, favorite_keys))
        raw_sensors.extend(self._normalize_nvidia_sensors(nvidia_snapshot or {}, favorite_keys))
        raw_sensors.extend(self._normalize_presentmon_sensors(presentmon_snapshot or {}, favorite_keys))

        context = self._context(raw_sensors)
        for row in raw_sensors:
            self._apply_validity(row, context)
        diagnostics: dict[str, Any] = {}

        cpu_temp, cpu_diag = self._best_cpu_temperature_sensor(raw_sensors)
        diagnostics["cpu_temperature"] = cpu_diag
        if cpu_temp:
            self._mark_selected(cpu_temp, "cpu_temp", headline=True)

        cpu_load = self._best_metric(raw_sensors, "cpu", "Load", ("cpu total", "total", "cpu", "package"))
        cpu_power = self._best_metric(raw_sensors, "cpu", "Power", ("package", "cpu package", "cpu", "core"))
        cpu_clock = self._best_metric(raw_sensors, "cpu", "Clock", ("effective", "average", "bus", "core", "cpu"))
        cpu_voltage = self._best_metric(raw_sensors, "cpu", "Voltage", ("vid", "vcore", "soc", "core", "cpu"))
        fan = self._best_metric(raw_sensors, "fans", "Fan", ("fan",))
        ram_load = self._best_metric(raw_sensors, "memory", "Load", ("memory", "ram", "used"))
        gpu_temp = self._best_metric(raw_sensors, "gpu", "Temperature", ("hot spot", "hotspot", "gpu core", "gpu", "temperature"))
        gpu_util = self._best_metric(raw_sensors, "gpu", "Load", ("gpu core", "utilization", "gpu"))
        gpu_power = self._best_metric(raw_sensors, "gpu", "Power", ("gpu", "package", "power"))
        gpu_clock = self._best_metric(raw_sensors, "gpu", "Clock", ("graphics", "core", "gpu"))
        vram_used = self._best_by_key(raw_sensors, "gpu_vram_used_mb")
        vram_total = self._best_by_key(raw_sensors, "gpu_vram_total_mb")
        fps = self._best_by_key(raw_sensors, "fps")
        frame_time = self._best_by_key(raw_sensors, "frame_time_ms")

        headline = self._build_headline(
            cpu_temp,
            cpu_load,
            cpu_power,
            cpu_clock,
            cpu_voltage,
            gpu_temp,
            gpu_util,
            gpu_power,
            gpu_clock,
            vram_used,
            vram_total,
            fps,
            frame_time,
            ram_load,
            fan,
            len(raw_sensors),
            sources,
            raw_sensors,
        )
        groups = self._groups(raw_sensors)
        cards = self._build_cards(headline)
        diagnostics["source_status"] = sources
        diagnostics["raw_sensor_count"] = len(raw_sensors)
        diagnostics["cpu_provider"] = self._cpu_provider_diagnostics(raw_sensors, headline)

        return {
            "ok": any(source.get("ok") for source in sources.values()) or bool(raw_sensors),
            "generated_local": datetime.now().isoformat(timespec="seconds"),
            "sources": sources,
            "headline": headline,
            "cards": cards,
            "groups": groups,
            "raw_sensors": raw_sensors,
            "diagnostics": diagnostics,
        }

    def _source_status(self, source_name: str, snapshot: dict[str, Any] | None) -> dict[str, Any]:
        if not snapshot:
            return {"ok": False, "source": source_name, "status": "not read", "error": None}
        error = snapshot.get("error")
        status = snapshot.get("status")
        ok = bool(snapshot.get("ok"))
        if source_name == "presentmon":
            error_text = str(error or "").lower()
            if snapshot.get("running"):
                status = "running"
            elif snapshot.get("empty_csv"):
                status = "no data"
                error = None
            elif "no presentmon csv" in error_text or "csv has no data" in error_text:
                status = "idle"
                error = None
            elif not status:
                status = "idle" if not ok else "ok"
        elif not status:
            status = "ok" if ok else "unavailable"
        return {
            "ok": ok,
            "source": snapshot.get("source") or source_name,
            "status": status,
            "error": error,
            "generated_local": snapshot.get("generated_local"),
            "sensor_count": snapshot.get("sensor_count"),
        }

    def _normalize_lhm_sensors(self, snapshot: dict[str, Any], favorite_keys: set[tuple[str, str, str, str]]) -> list[dict[str, Any]]:
        rows = []
        for index, row in enumerate(snapshot.get("sensors", []) or []):
            source = str(row.get("source") or "lhm")
            hardware = str(row.get("hardware") or "")
            hardware_type = str(row.get("hardware_type") or "")
            sensor_type = str(row.get("sensor_type") or "")
            name = str(row.get("name") or "")
            value = self._number(row.get("value"))
            category = self._category(hardware_type, sensor_type, hardware, name)
            subcategory = self._subcategory(category, hardware_type, sensor_type, hardware, name)
            unit = self._unit_for(sensor_type, name, hardware, category, subcategory)
            normalized_key = self._normalized_key(category, subcategory, sensor_type, name, hardware)
            key = self._favorite_key(source, hardware, sensor_type, name)
            rows.append(
                {
                    "source": source,
                    "provider": "LibreHardwareMonitor",
                    "hardware": hardware,
                    "hardware_type": hardware_type,
                    "sensor_type": sensor_type,
                    "name": name,
                    "value": value,
                    "unit": unit,
                    "min": self._number(row.get("min")),
                    "max": self._number(row.get("max")),
                    "sample_values": row.get("sample_values") or [],
                    "sample_nonzero_count": row.get("sample_nonzero_count"),
                    "stale_zero": bool(row.get("stale_zero")),
                    "category": category,
                    "subcategory": subcategory,
                    "normalized_key": normalized_key,
                    "display_name": self._display_name(hardware, name),
                    "display_value": self._display_value(value, unit),
                    "score": 0,
                    "confidence": "raw",
                    "selected_for": [],
                    "selected_for_headline": False,
                    "favorite": key in favorite_keys,
                    "notes": "LibreHardwareMonitor raw sensor",
                    "raw_index": index,
                }
            )
        return rows

    def _normalize_nvidia_sensors(self, snapshot: dict[str, Any], favorite_keys: set[tuple[str, str, str, str]]) -> list[dict[str, Any]]:
        if not snapshot.get("ok"):
            return []
        data = snapshot.get("data", {}) or {}
        rows = []
        field_map = {
            "temperature.gpu": ("Temperature", "GPU Temperature", "gpu_core_temp_c", "C"),
            "utilization.gpu": ("Load", "GPU Utilization", "gpu_core_load_percent", "%"),
            "utilization.memory": ("Load", "GPU Memory Utilization", "gpu_memory_load_percent", "%"),
            "power.draw": ("Power", "GPU Power", "gpu_package_power_w", "W"),
            "power.limit": ("Power", "GPU Power Limit", "gpu_power_limit_w", "W"),
            "clocks.current.graphics": ("Clock", "GPU Graphics Clock", "gpu_core_clock_mhz", "MHz"),
            "clocks.gr": ("Clock", "GPU Graphics Clock", "gpu_core_clock_mhz", "MHz"),
            "clocks.current.memory": ("Clock", "GPU Memory Clock", "gpu_memory_clock_mhz", "MHz"),
            "memory.used": ("Data", "VRAM Used", "gpu_vram_used_mb", "MB"),
            "memory.total": ("Data", "VRAM Total", "gpu_vram_total_mb", "MB"),
            "memory.free": ("Data", "VRAM Free", "gpu_vram_free_mb", "MB"),
        }
        for field, raw_value in data.items():
            if field not in field_map:
                continue
            sensor_type, name, normalized_key, unit = field_map[field]
            value = self._number(raw_value)
            key = self._favorite_key("nvidia-smi", "NVIDIA GPU", sensor_type, name)
            rows.append(
                {
                    "source": "nvidia-smi",
                    "provider": "nvidia-smi",
                    "hardware": str(data.get("name") or "NVIDIA GPU"),
                    "hardware_type": "Gpu",
                    "sensor_type": sensor_type,
                    "name": name,
                    "value": value,
                    "unit": unit,
                    "min": None,
                    "max": None,
                    "category": "gpu",
                    "subcategory": "dgpu",
                    "normalized_key": normalized_key,
                    "display_name": name,
                    "display_value": self._display_value(value, unit),
                    "score": 80,
                    "confidence": "adapter",
                    "selected_for": [],
                    "selected_for_headline": False,
                    "favorite": key in favorite_keys,
                    "notes": f"nvidia-smi field {field}",
                }
            )
        return rows

    def _normalize_presentmon_sensors(self, snapshot: dict[str, Any], favorite_keys: set[tuple[str, str, str, str]]) -> list[dict[str, Any]]:
        if not snapshot:
            return []
        rows = []
        mapping = [
            ("fps_average_sample", "FPS", "FPS", "fps"),
            ("fps", "FPS", "FPS", "fps"),
            ("frametime_ms_average_sample", "Frame Time", "ms", "frame_time_ms"),
            ("frame_time_ms", "Frame Time", "ms", "frame_time_ms"),
        ]
        for field, title, unit, key_name in mapping:
            if field not in snapshot:
                continue
            value = self._number(snapshot.get(field))
            if value is None:
                continue
            favorite_key = self._favorite_key("presentmon", "PresentMon", "Frame", title)
            rows.append(
                {
                    "source": "presentmon",
                    "provider": "PresentMon",
                    "hardware": str(snapshot.get("latest_process") or "PresentMon"),
                    "hardware_type": "FrameCapture",
                    "sensor_type": "Frame",
                    "name": title,
                    "value": value,
                    "unit": unit,
                    "min": None,
                    "max": None,
                    "category": "frames",
                    "subcategory": "frames",
                    "normalized_key": key_name,
                    "display_name": title,
                    "display_value": self._display_value(value, unit),
                    "score": 80,
                    "confidence": "csv",
                    "selected_for": [],
                    "selected_for_headline": False,
                    "favorite": favorite_key in favorite_keys,
                    "notes": f"PresentMon field {field}",
                }
            )
        return rows

    def _context(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        cpu_load_values = [
            self._number(row.get("value"))
            for row in rows
            if row.get("category") == "cpu" and str(row.get("sensor_type", "")).lower() == "load"
        ]
        cpu_load_values = [value for value in cpu_load_values if value is not None and value >= 0]
        gpu_load_values = [
            self._number(row.get("value"))
            for row in rows
            if row.get("category") == "gpu" and str(row.get("sensor_type", "")).lower() == "load"
        ]
        gpu_load_values = [value for value in gpu_load_values if value is not None and value >= 0]
        return {
            "cpu_load_percent": max(cpu_load_values) if cpu_load_values else None,
            "cpu_load_nonzero": any(value > 1 for value in cpu_load_values),
            "gpu_load_percent": max(gpu_load_values) if gpu_load_values else None,
        }

    def _apply_validity(self, row: dict[str, Any], context: dict[str, Any]) -> None:
        validity, reason = self.sensor_validity(row, context)
        row["validity"] = validity
        row["validity_reason"] = reason
        row["display_status"] = self._display_status(validity, reason)
        row["can_use_for_headline"] = validity == "valid" and self._number(row.get("value")) is not None
        row["can_use_for_card"] = row["can_use_for_headline"]
        row["display_value"] = self._display_value(row.get("value"), row.get("unit"))
        if validity != "valid":
            row["confidence"] = validity
            row["notes"] = f"{row.get('notes')}; {reason}".strip("; ")

    def sensor_validity(self, row: dict[str, Any], context: dict[str, Any]) -> tuple[str, str]:
        value = self._number(row.get("value"))
        category = str(row.get("category") or "")
        sensor_type = str(row.get("sensor_type") or "")
        name = str(row.get("name") or "")
        if value is None:
            return "unavailable", "Sensor did not provide a numeric value."
        st = sensor_type.lower()
        if st == "temperature":
            return self.is_valid_temperature(value, category, name)
        if st == "power":
            return self.is_valid_power(value, category, context)
        if st == "clock":
            return self.is_valid_clock(value, category, context)
        if st == "voltage":
            return self.is_valid_voltage(value, category, name)
        if st == "fan":
            if value < 0:
                return "invalid_value", "Fan RPM reported a negative value."
            if value <= 1:
                return "valid", "Fan sensor exists and currently reports stopped or hidden RPM."
            return "valid", "Fan RPM is valid."
        if row.get("category") == "frames" and value < 0:
            return "idle_no_capture", "PresentMon frame metric is idle or unavailable."
        if st in ("load", "data", "smalldata", "throughput", "frame"):
            if value < 0:
                return "invalid_value", f"{sensor_type} reported a negative value."
            return "valid", f"{sensor_type} value is valid."
        if value < 0:
            return "invalid_value", "Sensor reported a negative value."
        return "valid", "Sensor value is valid."

    def is_valid_temperature(self, value: float, category: str, name: str) -> tuple[str, str]:
        if value <= 1:
            return "invalid_value", f"invalid temperature: {name or 'temperature sensor'} reported {value:g} C, which is not a usable live temperature."
        if value >= 125:
            return "invalid_value", f"invalid temperature: {name or 'temperature sensor'} reported {value:g} C, which is outside the trusted range."
        return "valid", "Temperature is within the trusted range."

    def is_valid_power(self, value: float, category: str, context: dict[str, Any]) -> tuple[str, str]:
        if value < 0:
            return "invalid_value", "Power sensor reported a negative value."
        if category == "cpu" and value <= 0:
            if context.get("cpu_load_nonzero"):
                return "stale_zero", "CPU power reported 0 W while CPU load is nonzero."
            return "stale_zero", "CPU power reported 0 W; treating as provider stale-zero."
        return "valid", "Power value is valid."

    def is_valid_clock(self, value: float, category: str, context: dict[str, Any]) -> tuple[str, str]:
        if value < 0:
            return "invalid_value", "Clock sensor reported a negative value."
        if category == "cpu" and value <= 0:
            if context.get("cpu_load_nonzero"):
                return "stale_zero", "CPU clock reported 0 MHz while CPU load is nonzero."
            return "stale_zero", "CPU clock reported 0 MHz; treating as provider stale-zero."
        return "valid", "Clock value is valid."

    def is_valid_voltage(self, value: float, category: str, name: str) -> tuple[str, str]:
        if value <= 0:
            return "invalid_value", f"{name or 'voltage sensor'} reported a non-positive voltage."
        upper = 3.5 if category == "cpu" else 20.0
        if value > upper:
            return "invalid_value", f"{name or 'voltage sensor'} reported {value:g} V, outside expected range."
        return "valid", "Voltage value is valid."

    def _best_cpu_temperature_sensor(self, sensors: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        temp_rows = [row for row in sensors if str(row.get("sensor_type", "")).lower() == "temperature"]
        cpu_hw_temp_rows = [row for row in temp_rows if str(row.get("hardware_type", "")).lower() == "cpu"]
        accepted = []
        rejected = []
        for row in temp_rows:
            value = self._number(row.get("value"))
            text = self._sensor_text(row)
            if row.get("validity") != "valid":
                rejected.append(
                    {
                        "name": row.get("name"),
                        "hardware": row.get("hardware"),
                        "value": value,
                        "reason": row.get("validity_reason") or "invalid temperature",
                        "validity": row.get("validity"),
                    }
                )
                continue
            cpu_hw = str(row.get("hardware_type", "")).lower() == "cpu"
            cpu_like = cpu_hw or self._non_cpu_row_is_cpu_like(text)
            if not cpu_like:
                rejected.append({"name": row.get("name"), "hardware": row.get("hardware"), "value": value, "reason": "not CPU-like", "validity": "valid"})
                continue
            rank, reason = self._cpu_temp_rank(row)
            base = 0 if cpu_hw else 200
            score = base + rank
            accepted.append({"row": row, "score": score, "rank": rank, "value": value, "reason": reason if rank < 100 else "CPU fallback candidate"})

        if accepted:
            ranked = [item for item in accepted if item["rank"] < 100]
            pool = ranked if ranked else accepted
            if ranked:
                pool.sort(key=lambda item: (item["score"], -item["value"]))
            else:
                pool.sort(key=lambda item: (-item["value"], item["score"]))
            selected = pool[0]["row"]
            selected["score"] = 100 - min(pool[0]["score"], 99)
            selected["confidence"] = "selected"
            notes = set([str(selected.get("notes") or ""), pool[0]["reason"]])
            selected["notes"] = "; ".join(note for note in notes if note)
        else:
            selected = None

        failure = None if selected else "No valid CPU temperature candidate found."
        if not selected:
            invalid_cpu = [row for row in rejected if row.get("validity") == "invalid_value" and self._looks_cpu_related(row)]
            if invalid_cpu:
                first = invalid_cpu[0]
                failure = f"CPU temperature unavailable: {first.get('name')} returned {first.get('value')} C and was rejected."

        return selected, {
            "selected": self._diagnostic_row(selected) if selected else None,
            "total_temperature_sensors": len(temp_rows),
            "cpu_hardware_temperature_sensors": len(cpu_hw_temp_rows),
            "accepted_candidates": [
                {"name": item["row"].get("name"), "hardware": item["row"].get("hardware"), "value": item["value"], "score": item["score"], "reason": item["reason"], "validity": "valid"}
                for item in accepted
            ],
            "rejected_candidates": rejected,
            "failure_reason": failure,
        }

    def _best_metric(self, sensors: list[dict[str, Any]], category: str, sensor_type: str, keywords: tuple[str, ...]) -> dict[str, Any] | None:
        candidates = []
        for row in sensors:
            if str(row.get("category")) != category:
                continue
            if str(row.get("sensor_type", "")).lower() != sensor_type.lower():
                continue
            if not row.get("can_use_for_headline"):
                continue
            value = self._number(row.get("value"))
            if value is None or value < 0:
                continue
            text = self._sensor_text(row)
            rank = next((index for index, keyword in enumerate(keywords) if keyword in text), 100)
            source_priority = self._source_priority(row) if category == "gpu" else 0
            candidates.append((source_priority, rank, -value, row))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]))
        row = candidates[0][3]
        self._mark_selected(row, f"{category}_{sensor_type.lower()}")
        return row

    def _best_by_key(self, sensors: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
        candidates = [row for row in sensors if row.get("normalized_key") == key and row.get("can_use_for_headline")]
        if not candidates:
            return None
        if key.startswith("gpu_"):
            candidates.sort(key=lambda row: (self._source_priority(row), -(self._number(row.get("value")) or 0)))
            return candidates[0]
        return candidates[0]

    def _build_headline(
        self,
        cpu_temp: dict[str, Any] | None,
        cpu_load: dict[str, Any] | None,
        cpu_power: dict[str, Any] | None,
        cpu_clock: dict[str, Any] | None,
        cpu_voltage: dict[str, Any] | None,
        gpu_temp: dict[str, Any] | None,
        gpu_util: dict[str, Any] | None,
        gpu_power: dict[str, Any] | None,
        gpu_clock: dict[str, Any] | None,
        vram_used: dict[str, Any] | None,
        vram_total: dict[str, Any] | None,
        fps: dict[str, Any] | None,
        frame_time: dict[str, Any] | None,
        ram_load: dict[str, Any] | None,
        fan: dict[str, Any] | None,
        sensor_count: int,
        sources: dict[str, Any],
        raw_sensors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        cpu_temp_value = self._number(cpu_temp.get("value")) if cpu_temp else None
        cpu_load_value = self._number(cpu_load.get("value")) if cpu_load else None
        cpu_power_value = self._number(cpu_power.get("value")) if cpu_power else None
        cpu_clock_value = self._number(cpu_clock.get("value")) if cpu_clock else None
        cpu_voltage_value = self._number(cpu_voltage.get("value")) if cpu_voltage else None
        gpu_temp_value = self._number(gpu_temp.get("value")) if gpu_temp else None
        gpu_util_value = self._number(gpu_util.get("value")) if gpu_util else None
        gpu_power_value = self._number(gpu_power.get("value")) if gpu_power else None
        gpu_clock_value = self._number(gpu_clock.get("value")) if gpu_clock else None
        vram_used_value = self._number(vram_used.get("value")) if vram_used else None
        vram_total_value = self._number(vram_total.get("value")) if vram_total else None
        fps_value = self._number(fps.get("value")) if fps else None
        frame_time_value = self._number(frame_time.get("value")) if frame_time else None
        ram_load_value = self._number(ram_load.get("value")) if ram_load else None
        fan_value = self._number(fan.get("value")) if fan else None

        cpu_temp_display = self._cpu_temp_display(cpu_temp, cpu_temp_value)
        cpu_load_display = f"Load {cpu_load_value:.0f}%" if cpu_load_value is not None else None
        cpu_power_display = f"CPU power {cpu_power_value:.1f} W" if cpu_power_value is not None else "Power unavailable"
        cpu_clock_display = f"{cpu_clock_value:.0f} MHz" if cpu_clock_value is not None else "Clock unavailable"
        cpu_voltage_display = f"VID {cpu_voltage_value:.2f} V" if cpu_voltage_value is not None else None
        fan_display = f"Fan {fan_value:.0f} RPM" if fan_value is not None and fan_value > 1 else "Fan unavailable"
        sensors_display = f"{sensor_count} readings"

        if cpu_temp_value is not None:
            status_parts = [f"CPU {cpu_temp_display}"]
        elif cpu_load_value is not None:
            status_parts = [f"CPU Load {cpu_load_value:.0f}%", "Temp unavailable"]
        elif cpu_voltage_value is not None:
            status_parts = [f"CPU {cpu_voltage_value:.2f} V", "Temp unavailable"]
        else:
            status_parts = ["CPU telemetry partial", "Temp unavailable"]
        if cpu_power_value is None:
            status_parts.append("Power unavailable")
        elif cpu_power_display:
            status_parts.append(cpu_power_display)
        if fan_display:
            status_parts.append(fan_display)
        status_parts.append(sensors_display)

        fps_display = f"{fps_value:.0f} FPS" if fps_value is not None else "FPS idle"
        frame_display = f"{frame_time_value:.2f} ms" if frame_time_value is not None else None
        gpu_status = "GPU unavailable"
        if gpu_temp_value is not None or gpu_util_value is not None or gpu_power_value is not None:
            gpu_status = "GPU " + " | ".join(
                part
                for part in [
                    f"{gpu_temp_value:.0f} C" if gpu_temp_value is not None else None,
                    f"{gpu_util_value:.0f}%" if gpu_util_value is not None else None,
                    f"{gpu_power_value:.0f} W" if gpu_power_value is not None else None,
                ]
                if part
            )
        provider_health = self._provider_health(raw_sensors)

        return {
            "ok": any(source.get("ok") for source in sources.values()),
            "cpu_temp_c": cpu_temp_value,
            "cpu_temp_name": cpu_temp.get("name") if cpu_temp else None,
            "cpu_temp_hardware": cpu_temp.get("hardware") if cpu_temp else None,
            "cpu_temp_display": cpu_temp_display,
            "cpu_load_percent": cpu_load_value,
            "cpu_load_display": cpu_load_display,
            "cpu_power_w": cpu_power_value,
            "cpu_power_display": cpu_power_display,
            "cpu_clock_mhz": cpu_clock_value,
            "cpu_clock_display": cpu_clock_display,
            "cpu_voltage_v": cpu_voltage_value,
            "cpu_voltage_display": cpu_voltage_display,
            "cpu_provider_health": provider_health,
            "gpu_temp_c": gpu_temp_value,
            "gpu_temp_display": f"{gpu_temp_value:.0f} C" if gpu_temp_value is not None else "GPU temp unavailable",
            "gpu_util_percent": gpu_util_value,
            "gpu_power_w": gpu_power_value,
            "gpu_clock_mhz": gpu_clock_value,
            "vram_used_mb": vram_used_value,
            "vram_total_mb": vram_total_value,
            "fps": fps_value,
            "fps_display": fps_display,
            "frame_time_ms": frame_time_value,
            "frame_time_display": frame_display or "Frame time idle",
            "ram_load_percent": ram_load_value,
            "fan_rpm": fan_value,
            "fan_display": fan_display,
            "sensor_count": sensor_count,
            "sensors_display": sensors_display,
            "sensor_read_status": "ok" if any(source.get("ok") for source in sources.values()) else "unavailable",
            "status_display": " | ".join(status_parts),
            "gpu_status_display": gpu_status,
            "vram_status_display": f"VRAM {vram_used_value:.0f} / {vram_total_value:.0f} MB" if vram_used_value is not None and vram_total_value is not None else "VRAM n/a",
            "fps_status_display": fps_display,
        }

    def _build_cards(self, headline: dict[str, Any]) -> list[dict[str, Any]]:
        card_specs = [
            ("CPU Temperature", "cpu_temp_c", "C", "cpu_temp_display", None, "temp"),
            ("CPU Load", "cpu_load_percent", "%", "cpu_load_display", 100, "percent"),
            ("CPU Voltage", "cpu_voltage_v", "V", "cpu_voltage_display", None, "voltage"),
            ("GPU Temperature", "gpu_temp_c", "C", "gpu_temp_display", None, "temp"),
            ("GPU Utilization", "gpu_util_percent", "%", None, 100, "percent"),
            ("GPU Power", "gpu_power_w", "W", None, None, "power"),
            ("VRAM Used", "vram_used_mb", "MB", None, headline.get("vram_total_mb"), "data"),
            ("FPS", "fps", "FPS", "fps_display", None, "fps"),
            ("Frame Time", "frame_time_ms", "ms", "frame_time_display", None, "frame"),
            ("RAM Load", "ram_load_percent", "%", None, 100, "percent"),
            ("Fan", "fan_rpm", "RPM", "fan_display", None, "fan"),
        ]
        cards = []
        for title, key, unit, display_key, max_value, kind in card_specs:
            value = headline.get(key)
            display = headline.get(display_key) if display_key else None
            tone = self._tone_for(kind, self._number(value), title)
            progress = self._progress(self._number(value), self._number(max_value))
            cards.append(
                {
                    "title": title,
                    "key": key,
                    "value": value,
                    "value_display": display or self._display_value(value, unit),
                    "unit": unit,
                    "subtitle": display or "",
                    "tone": tone,
                    "progress": progress,
                }
            )
        return cards

    def _groups(self, sensors: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        groups = {key: [] for key in ["cpu", "gpu", "memory", "fans", "storage", "network", "battery_power", "motherboard", "frames", "other"]}
        for row in sensors:
            groups.setdefault(row.get("category") or "other", []).append(row)
        return groups

    def _category(self, hardware_type: str, sensor_type: str, hardware: str, name: str) -> str:
        text = " ".join([hardware_type, sensor_type, hardware, name]).lower()
        hw = hardware_type.lower()
        st = sensor_type.lower()
        if hw == "cpu":
            return "cpu"
        if hw.startswith("gpu") or any(term in text for term in ("nvidia", "rtx", "geforce", "amd radeon", "radeon 860m", "gpu")):
            if "system memory" not in text and "generic memory" not in text:
                return "gpu"
        if hw in ("memory", "ram") or "generic memory" in text or "system memory" in text or "ram" in text:
            return "memory"
        if st == "fan" or "fan" in text:
            return "fans"
        if hw in ("storage", "hdd", "ssd") or any(term in text for term in ("nvme", "ssd", "hdd", "drive")):
            return "storage"
        if "network" in text or hw == "network":
            return "network"
        if "battery" in text or "ac adapter" in text or hw in ("battery", "power"):
            return "battery_power"
        if "motherboard" in text or "controller" in text or hw in ("motherboard", "superio"):
            return "motherboard"
        return "other"

    def _subcategory(self, category: str, hardware_type: str, sensor_type: str, hardware: str, name: str) -> str:
        text = " ".join([hardware_type, sensor_type, hardware, name]).lower()
        name_text = name.lower()
        hw = hardware_type.lower()
        if category == "gpu":
            if "vram" in text or "memory used" in text or "memory total" in text:
                return "gpu_vram"
            if "junction" in text or "memory" in text:
                return "gpu_memory"
            if "hot spot" in text or "hotspot" in text:
                return "gpu_hotspot"
            if "pcie" in text or " bus" in text or name_text in ("rx", "tx") or name_text.startswith("rx ") or name_text.startswith("tx "):
                return "gpu_bus"
            if "engine" in text:
                return "gpu_engine"
            if "nvidia" in hw or "nvidia" in text or "rtx" in text or "geforce" in text:
                return "dgpu"
            if "amd" in hw or "radeon" in text:
                return "igpu"
            return "gpu"
        return category

    def _normalized_key(self, category: str, subcategory: str, sensor_type: str, name: str, hardware: str) -> str:
        text = " ".join([hardware, name]).lower()
        st = sensor_type.lower()
        if category == "cpu":
            if st == "temperature":
                return "cpu_temperature_c"
            if st == "load":
                return "cpu_load_percent"
            if st == "power":
                return "cpu_power_w"
            if st == "clock":
                return "cpu_clock_mhz"
            if st == "voltage":
                return "cpu_voltage_v"
        if category == "gpu":
            if st == "temperature":
                if "junction" in text:
                    return "gpu_memory_junction_temp_c"
                if "hot spot" in text or "hotspot" in text:
                    return "gpu_hotspot_temp_c"
                return "gpu_core_temp_c"
            if st == "clock":
                if "memory" in text:
                    return "gpu_memory_clock_mhz"
                return "gpu_core_clock_mhz"
            if st == "load":
                if "memory" in text:
                    return "gpu_memory_load_percent"
                return "gpu_core_load_percent"
            if st == "power":
                return "gpu_package_power_w"
            if st in ("data", "smalldata"):
                if "used" in text:
                    return "gpu_vram_used_mb"
                if "free" in text:
                    return "gpu_vram_free_mb"
                if "total" in text or "dedicated" in text:
                    return "gpu_vram_total_mb"
            if st == "throughput":
                if "rx" in text or "read" in text:
                    return "gpu_pcie_rx_bps"
                if "tx" in text or "write" in text:
                    return "gpu_pcie_tx_bps"
        if category == "memory":
            if st == "load":
                return "ram_load_percent"
            if st in ("data", "smalldata") and "used" in text:
                return "ram_used_gb"
            if st in ("data", "smalldata") and ("available" in text or "free" in text):
                return "ram_available_gb"
        if category == "fans":
            return "fan_rpm"
        if category == "storage" and st == "temperature":
            return "storage_temperature_c"
        return "_".join(part for part in [category, st, self._slug(text)[:36]] if part)

    def _cpu_provider_diagnostics(self, sensors: list[dict[str, Any]], headline: dict[str, Any]) -> dict[str, Any]:
        cpu_rows = [row for row in sensors if row.get("category") == "cpu"]
        status = {
            "provider": "LibreHardwareMonitor",
            "status": "partial" if cpu_rows else "unavailable",
            "cpu_load_valid": headline.get("cpu_load_percent") is not None,
            "cpu_temp_valid": headline.get("cpu_temp_c") is not None,
            "cpu_power_valid": headline.get("cpu_power_w") is not None,
            "cpu_clock_valid": headline.get("cpu_clock_mhz") is not None,
            "cpu_voltage_valid": headline.get("cpu_voltage_v") is not None,
            "stale_zero_count": len([row for row in cpu_rows if row.get("validity") == "stale_zero"]),
            "invalid_count": len([row for row in cpu_rows if row.get("validity") == "invalid_value"]),
        }
        if status["cpu_load_valid"] and status["cpu_voltage_valid"] and not status["cpu_temp_valid"]:
            status["summary"] = "CPU telemetry is partial: load and voltage are valid, but temperature/power/clock are not usable from this provider."
        else:
            status["summary"] = "CPU telemetry provider status computed from normalized LibreHardwareMonitor rows."
        return status

    def _provider_health(self, sensors: list[dict[str, Any]]) -> str:
        cpu_rows = [row for row in sensors if row.get("category") == "cpu"]
        if not cpu_rows:
            return "unavailable"
        has_valid = any(row.get("validity") == "valid" for row in cpu_rows)
        has_bad = any(row.get("validity") in ("stale_zero", "invalid_value", "unavailable") for row in cpu_rows)
        if has_valid and has_bad:
            return "partial"
        if has_valid:
            return "ok"
        return "unavailable"

    def _source_priority(self, row: dict[str, Any]) -> int:
        source = str(row.get("source") or "").lower()
        text = self._sensor_text(row)
        if source == "nvidia-smi":
            return 0
        if "nvidia" in text or "rtx" in text or "geforce" in text:
            return 1
        if row.get("subcategory") == "dgpu":
            return 2
        return 3

    def _mark_selected(self, row: dict[str, Any], key: str, headline: bool = False) -> None:
        selected = set(row.get("selected_for") or [])
        selected.add(key)
        row["selected_for"] = sorted(selected)
        if headline:
            row["selected_for_headline"] = True

    def _cpu_temp_rank(self, row: dict[str, Any]) -> tuple[int, str]:
        text = self._sensor_text(row)
        for keyword, rank, reason in self.CPU_TEMP_PRIORITY:
            if keyword in text:
                return rank, reason
        return 100, "valid CPU-related temperature fallback"

    def _non_cpu_row_is_cpu_like(self, text: str) -> bool:
        strong_terms = ("cpu", "processor", "tctl", "tdie", "p-core", "e-core", "ia cores", "gt cores")
        if any(term in text for term in strong_terms):
            return True
        if "intel" in text and any(term in text for term in ("package", "core", "die")):
            return True
        if "amd" in text and any(term in text for term in ("package", "core", "die")):
            return True
        return False

    def _looks_cpu_related(self, row: dict[str, Any]) -> bool:
        return str(row.get("hardware_type", "")).lower() == "cpu" or self._non_cpu_row_is_cpu_like(self._sensor_text(row))

    def _sensor_text(self, row: dict[str, Any]) -> str:
        return " ".join([str(row.get("hardware", "")), str(row.get("hardware_type", "")), str(row.get("name", ""))]).lower()

    def _diagnostic_row(self, row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        return {
            "source": row.get("source"),
            "provider": row.get("provider"),
            "hardware": row.get("hardware"),
            "hardware_type": row.get("hardware_type"),
            "sensor_type": row.get("sensor_type"),
            "name": row.get("name"),
            "value": row.get("value"),
            "unit": row.get("unit"),
            "score": row.get("score"),
            "validity": row.get("validity"),
            "validity_reason": row.get("validity_reason"),
            "notes": row.get("notes"),
        }

    def _display_name(self, hardware: str, name: str) -> str:
        if hardware and name:
            return f"{hardware} - {name}"
        return hardware or name or "Unnamed sensor"

    def _display_value(self, value: Any, unit: str | None) -> str:
        number = self._number(value)
        if number is None:
            return "unavailable" if value in (None, "") else str(value)
        if unit in ("%", "C", "W", "MHz", "RPM", "MB", "GB", "FPS", "V"):
            if unit == "V":
                return f"{number:.2f} V" if abs(number - round(number)) >= 0.005 else f"{number:.0f} V"
            if unit == "GB":
                return f"{number:.1f} GB" if abs(number - round(number)) >= 0.05 else f"{number:.0f} GB"
            if abs(number - round(number)) < 0.05:
                return f"{number:.0f} {unit}".strip()
            return f"{number:.1f} {unit}".strip()
        if unit == "ms":
            return f"{number:.2f} ms"
        return f"{number:.0f}" if abs(number - round(number)) < 0.05 else f"{number:.1f}"

    def _cpu_temp_display(self, row: dict[str, Any] | None, value: float | None) -> str:
        if value is None:
            return "CPU temp unavailable"
        suffix = self._temperature_suffix(str(row.get("name") or "")) if row else ""
        return f"{value:.0f} C {suffix}".strip()

    def _temperature_suffix(self, name: str) -> str:
        lowered = name.lower()
        replacements = [
            ("cpu package", "Package"),
            ("package", "Package"),
            ("core max", "Core Max"),
            ("p-core max", "P-Core Max"),
            ("e-core max", "E-Core Max"),
            ("tdie", "Tdie"),
            ("tctl", "Tctl"),
            ("average", "Average"),
            ("cpu die", "Die"),
        ]
        for needle, label in replacements:
            if needle in lowered:
                return label
        if lowered in ("cpu", "temperature"):
            return ""
        cleaned = name.replace("#", "").strip()
        if cleaned.lower().startswith("cpu "):
            cleaned = cleaned[4:].strip()
        return cleaned

    def _unit_for(self, sensor_type: str, name: str, hardware: str = "", category: str = "", subcategory: str = "") -> str:
        st = sensor_type.lower()
        text = " ".join([hardware, name]).lower()
        if st == "temperature":
            return "C"
        if st == "load":
            return "%"
        if st == "power":
            return "W"
        if st == "clock":
            return "MHz"
        if st == "fan":
            return "RPM"
        if st == "voltage":
            return "V"
        if st in ("data", "smalldata"):
            if category == "memory" and ("generic memory" in text or "system memory" in text or "memory used" in text or "memory available" in text):
                return "GB"
            return "MB"
        if st == "throughput":
            return "B/s"
        if "time" in name.lower():
            return "ms"
        return ""

    def _display_status(self, validity: str, reason: str) -> str:
        if validity == "valid":
            return "valid"
        if validity == "stale_zero":
            return "unavailable/stale zero"
        if validity == "invalid_value":
            return "invalid value"
        return validity.replace("_", " ")

    def _tone_for(self, kind: str, value: float | None, title: str) -> str:
        if value is None:
            return "unavailable"
        if kind == "temp":
            if value >= 95:
                return "danger"
            if value >= 85:
                return "warn"
            return "safe"
        if kind == "percent":
            if value >= 95:
                return "danger"
            if value >= 80:
                return "warn"
            return "safe"
        return "normal"

    def _progress(self, value: float | None, max_value: float | None) -> float | None:
        if value is None or max_value is None or max_value <= 0:
            return None
        return max(0.0, min(100.0, (value / max_value) * 100.0))

    def _number(self, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text or text.lower() in ("n/a", "na", "none", "unavailable", "[not supported]"):
            return None
        for token in ("%", "C", "W", "MHz", "RPM", "MB", "GB", "ms", "FPS", "V"):
            text = text.replace(token, "")
        text = text.strip()
        try:
            return float(text)
        except ValueError:
            return None

    def _favorite_keys(self, favorites: dict[str, Any]) -> set[tuple[str, str, str, str]]:
        keys = set()
        for item in favorites.get("favorites", []) or []:
            keys.add(self._favorite_key(item.get("source"), item.get("hardware"), item.get("sensor_type"), item.get("name")))
        return keys

    def _favorite_key(self, source: Any, hardware: Any, sensor_type: Any, name: Any) -> tuple[str, str, str, str]:
        return (str(source or "").lower(), str(hardware or "").lower(), str(sensor_type or "").lower(), str(name or "").lower())

    def _slug(self, text: str) -> str:
        chars = []
        for char in text.lower():
            chars.append(char if char.isalnum() else "_")
        return "_".join(part for part in "".join(chars).split("_") if part)
