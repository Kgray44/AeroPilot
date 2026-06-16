from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class DryRunPreview:
    command: list[str]
    working_directory: str | None
    risk_level: str
    explanation: str
    admin_may_be_required: bool
    backup_required: bool
    phase2_reason_not_executed: str = "Phase 2 is read-only/dry-run. This command is a preview only."

    def to_dict(self) -> dict:
        return asdict(self)

    def command_line(self) -> str:
        parts = []
        for part in self.command:
            text = str(part)
            if " " in text or '"' in text:
                text = '"' + text.replace('"', '\\"') + '"'
            parts.append(text)
        return " ".join(parts)


def msi_profile_preview(executable: str | None, slot: int) -> DryRunPreview:
    exe = executable or "MSIAfterburner.exe"
    return DryRunPreview(
        command=[exe, f"-Profile{slot}"],
        working_directory=str(Path(exe).parent) if "\\" in exe or "/" in exe else None,
        risk_level="Medium",
        explanation=(
            f"Dry-run preview for MSI Afterburner profile slot {slot}. "
            "Wrong slots may apply unintended GPU voltage/frequency curves."
        ),
        admin_may_be_required=False,
        backup_required=True,
    )


def powercfg_setting_preview(
    scheme_guid: str,
    subgroup_guid: str,
    setting_guid: str,
    value: int | str,
    target: str,
    risk_level: str,
) -> DryRunPreview:
    switch = "/setacvalueindex" if target.upper() == "AC" else "/setdcvalueindex"
    return DryRunPreview(
        command=["powercfg", switch, scheme_guid, subgroup_guid, setting_guid, str(value)],
        working_directory=None,
        risk_level=risk_level,
        explanation=f"Dry-run preview for a future {target.upper()} CPU power setting write.",
        admin_may_be_required=True,
        backup_required=True,
    )
