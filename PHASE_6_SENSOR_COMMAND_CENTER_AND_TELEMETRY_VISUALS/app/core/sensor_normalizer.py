from __future__ import annotations

from datetime import datetime
from typing import Any


class SensorNormalizer:
    """Convert live adapter snapshots into one UI-friendly telemetry model."""

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

    def normalize(
        self,
        lhm_snapshot: dict[str, Any] | None = None,
        nvidia_snapshot: dict[str, Any] | None = None,
        presentmon_snapshot: dict[str, Any] | None = None,
        favorites: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        favorite_keys = self._favorite_keys(favorites or {})
        raw_sensors: list[dict[str, Any]] = []
        diagnostics: dict[str, Any] = {}
        sources = {
            "lhm": self._source_status(lhm_snapshot),
            "nvidia_smi": self._source_status(nvidia_snapshot),
            "presentmon": self._source_status(presentmon_snapshot),
        }

        raw_sensors.extend(self._normalize_lhm_sensors(lhm_snapshot or {}, favorite_keys))
        raw_sensors.extend(self._normalize_nvidia_sensors(nvidia_snapshot or {}, favorite_keys))
        raw_sensors.extend(self._normalize_presentmon_sensors(presentmon_snapshot or {}, favorite_keys))

        cpu_temp, cpu_diag = self._best_cpu_temperature_sensor(raw_sensors)
        diagnostics["cpu_temperature"] = cpu_diag
        if cpu_temp:
            cpu_temp["selected_for_headline"] = True
            selected = set(cpu_temp.get("selected_for") or [])
            selected.add("cpu_temp")
            cpu_temp["selected_for"] = sorted(selected)

        cpu_load = self._best_metric(raw_sensors, "cpu", "Load", ("cpu total", "total", "cpu", "package"))
        cpu_power = self._best_metric(raw_sensors, "cpu", "Power", ("package", "cpu package", "cpu", "core"))
        cpu_clock = self._best_metric(raw_sensors, "cpu", "Clock", ("effective", "average", "bus", "core", "cpu"))
        fan = self._best_metric(raw_sensors, "fans", "Fan", ("fan",))
        ram_load = self._best_metric(raw_sensors, "memory", "Load", ("memory", "ram", "used"))
        gpu_temp = self._best_metric(raw_sensors, "gpu", "Temperature", ("hot spot", "gpu core", "gpu", "temperature"))
        gpu_util = self._best_metric(raw_sensors, "gpu", "Load", ("gpu core", "utilization", "gpu"))
        gpu_power = self._best_metric(raw_sensors, "gpu", "Power", ("gpu", "power"))
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
        )
        groups = self._groups(raw_sensors)
        cards = self._build_cards(headline)
        diagnostics["source_status"] = sources
        diagnostics["raw_sensor_count"] = len(raw_sensors)

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

    def _source_status(self, snapshot: dict[str, Any] | None) -> dict[str, Any]:
        if not snapshot:
            return {"ok": False, "status": "not read"}
        return {
            "ok": bool(snapshot.get("ok")),
            "source": snapshot.get("source"),
            "error": snapshot.get("error"),
            "generated_local": snapshot.get("generated_local"),
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
            unit = self._unit_for(sensor_type, name)
            category = self._category(hardware_type, sensor_type, hardware, name)
            normalized_key = self._normalized_key(category, sensor_type, name, hardware)
            key = self._favorite_key(source, hardware, sensor_type, name)
            rows.append(
                {
                    "source": source,
                    "hardware": hardware,
                    "hardware_type": hardware_type,
                    "sensor_type": sensor_type,
                    "name": name,
                    "value": value,
                    "unit": unit,
                    "min": self._number(row.get("min")),
                    "max": self._number(row.get("max")),
                    "category": category,
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
            "temperature.gpu": ("Temperature", "GPU Temperature", "gpu_temp_c", "C"),
            "utilization.gpu": ("Load", "GPU Utilization", "gpu_util_percent", "%"),
            "utilization.memory": ("Load", "GPU Memory Utilization", "gpu_memory_util_percent", "%"),
            "power.draw": ("Power", "GPU Power", "gpu_power_w", "W"),
            "power.limit": ("Power", "GPU Power Limit", "gpu_power_limit_w", "W"),
            "clocks.current.graphics": ("Clock", "GPU Graphics Clock", "gpu_clock_mhz", "MHz"),
            "clocks.gr": ("Clock", "GPU Graphics Clock", "gpu_clock_mhz", "MHz"),
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
                    "hardware": str(data.get("name") or "NVIDIA GPU"),
                    "hardware_type": "Gpu",
                    "sensor_type": sensor_type,
                    "name": name,
                    "value": value,
                    "unit": unit,
                    "min": None,
                    "max": None,
                    "category": "gpu",
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
                    "hardware": str(snapshot.get("latest_process") or "PresentMon"),
                    "hardware_type": "FrameCapture",
                    "sensor_type": "Frame",
                    "name": title,
                    "value": value,
                    "unit": unit,
                    "min": None,
                    "max": None,
                    "category": "frames",
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

    def _best_cpu_temperature_sensor(self, sensors: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        temp_rows = [row for row in sensors if str(row.get("sensor_type", "")).lower() == "temperature"]
        cpu_hw_temp_rows = [row for row in temp_rows if str(row.get("hardware_type", "")).lower() == "cpu"]
        accepted = []
        rejected = []
        for row in temp_rows:
            value = self._number(row.get("value"))
            text = self._sensor_text(row)
            if value is None:
                rejected.append({"name": row.get("name"), "hardware": row.get("hardware"), "value": row.get("value"), "reason": "missing numeric value"})
                continue
            if value <= 1 or value >= 125:
                rejected.append({"name": row.get("name"), "hardware": row.get("hardware"), "value": value, "reason": "invalid temperature outside 1-125 C"})
                continue
            cpu_hw = str(row.get("hardware_type", "")).lower() == "cpu"
            cpu_like = cpu_hw or self._non_cpu_row_is_cpu_like(text)
            if not cpu_like:
                rejected.append({"name": row.get("name"), "hardware": row.get("hardware"), "value": value, "reason": "not CPU-like"})
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

        return selected, {
            "selected": self._diagnostic_row(selected) if selected else None,
            "total_temperature_sensors": len(temp_rows),
            "cpu_hardware_temperature_sensors": len(cpu_hw_temp_rows),
            "accepted_candidates": [
                {"name": item["row"].get("name"), "hardware": item["row"].get("hardware"), "value": item["value"], "score": item["score"], "reason": item["reason"]}
                for item in accepted
            ],
            "rejected_candidates": rejected,
            "failure_reason": None if selected else "No valid CPU temperature candidate found.",
        }

    def _best_metric(self, sensors: list[dict[str, Any]], category: str, sensor_type: str, keywords: tuple[str, ...]) -> dict[str, Any] | None:
        candidates = []
        for row in sensors:
            if str(row.get("category")) != category:
                continue
            if str(row.get("sensor_type", "")).lower() != sensor_type.lower():
                continue
            value = self._number(row.get("value"))
            if value is None or value < 0:
                continue
            text = self._sensor_text(row)
            rank = next((index for index, keyword in enumerate(keywords) if keyword in text), 100)
            candidates.append((rank, -value, row))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]))
        row = candidates[0][2]
        selected = set(row.get("selected_for") or [])
        selected.add(f"{category}_{sensor_type.lower()}")
        row["selected_for"] = sorted(selected)
        return row

    def _best_by_key(self, sensors: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
        for row in sensors:
            if row.get("normalized_key") == key and self._number(row.get("value")) is not None:
                return row
        return None

    def _build_headline(
        self,
        cpu_temp: dict[str, Any] | None,
        cpu_load: dict[str, Any] | None,
        cpu_power: dict[str, Any] | None,
        cpu_clock: dict[str, Any] | None,
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
    ) -> dict[str, Any]:
        cpu_temp_value = self._number(cpu_temp.get("value")) if cpu_temp else None
        cpu_load_value = self._number(cpu_load.get("value")) if cpu_load else None
        cpu_power_value = self._number(cpu_power.get("value")) if cpu_power else None
        cpu_clock_value = self._number(cpu_clock.get("value")) if cpu_clock else None
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
        cpu_power_display = f"CPU power {cpu_power_value:.1f} W" if cpu_power_value is not None else None
        cpu_clock_display = f"{cpu_clock_value:.0f} MHz" if cpu_clock_value is not None else None
        fan_display = f"Fan {fan_value:.0f} RPM" if fan_value is not None and fan_value > 1 else "Fan unavailable"
        sensors_display = f"{sensor_count} readings"

        status_parts = [f"CPU {cpu_temp_display}" if cpu_temp_value is not None else "CPU temp unavailable"]
        if cpu_load_display:
            status_parts.append(cpu_load_display)
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
            ("CPU Power", "cpu_power_w", "W", "cpu_power_display", None, "power"),
            ("CPU Clock", "cpu_clock_mhz", "MHz", "cpu_clock_display", None, "clock"),
            ("GPU Temperature", "gpu_temp_c", "C", "gpu_temp_display", None, "temp"),
            ("GPU Utilization", "gpu_util_percent", "%", None, 100, "percent"),
            ("GPU Power", "gpu_power_w", "W", None, None, "power"),
            ("GPU Clock", "gpu_clock_mhz", "MHz", None, None, "clock"),
            ("VRAM Used", "vram_used_mb", "MB", None, headline.get("vram_total_mb"), "data"),
            ("FPS", "fps", "FPS", "fps_display", None, "fps"),
            ("Frame Time", "frame_time_ms", "ms", "frame_time_display", None, "frame"),
            ("RAM Load", "ram_load_percent", "%", None, 100, "percent"),
            ("Fan", "fan_rpm", "RPM", "fan_display", None, "fan"),
            ("Sensor Count", "sensor_count", "", "sensors_display", None, "count"),
            ("Read Status", "sensor_read_status", "", None, None, "status"),
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
        if hw == "gpu":
            return "gpu"
        if hw in ("memory", "ram") or "memory" in text or "ram" in text:
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

    def _normalized_key(self, category: str, sensor_type: str, name: str, hardware: str) -> str:
        text = " ".join([hardware, name]).lower()
        st = sensor_type.lower()
        if category == "cpu" and st == "temperature":
            return "cpu_temperature_c"
        if category == "cpu" and st == "load":
            return "cpu_load_percent"
        if category == "cpu" and st == "power":
            return "cpu_power_w"
        if category == "cpu" and st == "clock":
            return "cpu_clock_mhz"
        if category == "memory" and st == "load":
            return "ram_load_percent"
        if category == "fans":
            return "fan_rpm"
        if category == "storage" and st == "temperature":
            return "storage_temperature_c"
        return "_".join(part for part in [category, st, self._slug(text)[:36]] if part)

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

    def _sensor_text(self, row: dict[str, Any]) -> str:
        return " ".join([str(row.get("hardware", "")), str(row.get("hardware_type", "")), str(row.get("name", ""))]).lower()

    def _diagnostic_row(self, row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        return {
            "source": row.get("source"),
            "hardware": row.get("hardware"),
            "hardware_type": row.get("hardware_type"),
            "sensor_type": row.get("sensor_type"),
            "name": row.get("name"),
            "value": row.get("value"),
            "score": row.get("score"),
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
        if unit in ("%", "C", "W", "MHz", "RPM", "MB", "FPS"):
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

    def _unit_for(self, sensor_type: str, name: str) -> str:
        st = sensor_type.lower()
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
        if st == "data":
            return "MB"
        if "time" in name.lower():
            return "ms"
        return ""

    def _tone_for(self, kind: str, value: float | None, title: str) -> str:
        if value is None and kind not in ("count", "status"):
            return "unavailable"
        if kind == "temp" and value is not None:
            if value >= 95:
                return "danger"
            if value >= 85:
                return "warn"
            return "safe"
        if kind == "percent" and value is not None:
            if value >= 95:
                return "danger"
            if value >= 80:
                return "warn"
            return "safe"
        if kind == "status":
            return "safe" if str(value).lower() == "ok" else "unavailable"
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
        for token in ("%", "C", "W", "MHz", "RPM", "MB", "ms", "FPS"):
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
