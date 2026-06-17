from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Callable


SnapshotProvider = Callable[[], dict[str, Any]]


@dataclass
class ProviderStatus:
    provider_id: str
    provider_name: str
    enabled: bool
    attempted: bool
    available: bool
    status: str
    reason: str = ""
    last_probe_time: str | None = None
    sensor_count: int = 0
    valid_sensor_count: int = 0
    rejected_sensor_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TelemetryProviderRegistry:
    """Read-only telemetry provider registry.

    Providers return snapshots with a `sensors` list. The registry does not
    modify hardware or app state; it only records whether each provider was
    attempted and why it did or did not produce sensors.
    """

    def __init__(self) -> None:
        self._providers: dict[str, dict[str, Any]] = {}

    def register_static_provider(
        self,
        provider_id: str,
        provider_name: str,
        callback: SnapshotProvider,
        enabled: bool = True,
    ) -> None:
        self._providers[provider_id] = {
            "provider_id": provider_id,
            "provider_name": provider_name,
            "callback": callback,
            "enabled": bool(enabled),
        }

    def refresh(self) -> dict[str, Any]:
        snapshots: dict[str, dict[str, Any]] = {}
        statuses: dict[str, ProviderStatus] = {}
        for provider_id, entry in self._providers.items():
            provider_name = str(entry.get("provider_name") or provider_id)
            if not entry.get("enabled", True):
                statuses[provider_id] = ProviderStatus(
                    provider_id=provider_id,
                    provider_name=provider_name,
                    enabled=False,
                    attempted=False,
                    available=False,
                    status="not_configured",
                    reason="Provider disabled in app configuration.",
                    last_probe_time=None,
                )
                continue
            probe_time = datetime.now().isoformat(timespec="seconds")
            try:
                snapshot = entry["callback"]() or {}
            except Exception as exc:
                snapshot = {"ok": False, "error": str(exc), "sensors": []}
            snapshot.setdefault("provider_id", provider_id)
            snapshot.setdefault("provider_name", provider_name)
            snapshots[provider_id] = snapshot
            statuses[provider_id] = self.status_from_snapshot(provider_id, provider_name, True, True, probe_time, snapshot)
        return {"snapshots": snapshots, "provider_statuses": statuses}

    @staticmethod
    def status_from_snapshot(
        provider_id: str,
        provider_name: str,
        enabled: bool,
        attempted: bool,
        probe_time: str | None,
        snapshot: dict[str, Any] | None,
    ) -> ProviderStatus:
        snapshot = snapshot or {}
        sensors = snapshot.get("sensors") or []
        valid_count = len([row for row in sensors if row.get("validity") == "valid"])
        rejected_count = len([row for row in sensors if row.get("validity") in ("invalid_value", "stale_zero", "unavailable", "read_error")])
        explicit_status = str(snapshot.get("status") or "").strip()
        error = str(snapshot.get("error") or snapshot.get("reason") or "").strip()
        available = bool(snapshot.get("ok")) or bool(sensors)
        if explicit_status:
            status = explicit_status
        elif available and sensors:
            status = "ok"
        elif available:
            status = "partial"
        elif error:
            status = "unavailable"
        else:
            status = "unavailable"
        reason = error or str(snapshot.get("notes") or "")
        return ProviderStatus(
            provider_id=provider_id,
            provider_name=provider_name,
            enabled=enabled,
            attempted=attempted,
            available=available,
            status=status,
            reason=reason,
            last_probe_time=probe_time,
            sensor_count=len(sensors),
            valid_sensor_count=valid_count,
            rejected_sensor_count=rejected_count,
        )
