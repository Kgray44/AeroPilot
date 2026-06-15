from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.app_paths import AppPaths
from app.core.config_loader import load_json, save_json_inside_phase3


@dataclass
class ControlSurface:
    paths: AppPaths
    manifest: dict[str, Any]
    coverage_matrix: dict[str, Any]
    action_catalog: dict[str, Any]
    restore_catalog: dict[str, Any]
    unsupported: dict[str, Any]
    app_config: dict[str, Any]
    cpu_presets: dict[str, Any]
    gpu_profiles: dict[str, Any]
    game_rules: dict[str, Any]
    combined_presets: dict[str, Any]

    @classmethod
    def load(cls, paths: AppPaths | None = None) -> "ControlSurface":
        app_paths = paths or AppPaths.discover()
        return cls(
            paths=app_paths,
            manifest=load_json(app_paths.config_dir / "control_surface_manifest.json", {"controls": []}),
            coverage_matrix=load_json(app_paths.config_dir / "ui_coverage_matrix.json", {"coverage": []}),
            action_catalog=load_json(app_paths.config_dir / "action_catalog.json", {"actions": []}),
            restore_catalog=load_json(app_paths.config_dir / "restore_requirement_catalog.json", {"requirements": []}),
            unsupported=load_json(app_paths.config_dir / "unsupported_or_blocked_controls.json", {"controls": []}),
            app_config=load_json(app_paths.config_dir / "app_config.json", {}),
            cpu_presets=load_json(app_paths.presets_dir / "cpu_presets.json", {"presets": []}),
            gpu_profiles=load_json(app_paths.presets_dir / "gpu_profiles.json", {"slots": []}),
            game_rules=load_json(app_paths.presets_dir / "game_rules.json", {"rules": []}),
            combined_presets=load_json(app_paths.presets_dir / "combined_presets.json", {"combined_presets": [], "experiment_plans": []}),
        )

    @property
    def controls(self) -> list[dict[str, Any]]:
        return list(self.manifest.get("controls", []))

    @property
    def coverage_rows(self) -> list[dict[str, Any]]:
        return list(self.coverage_matrix.get("coverage", []))

    @property
    def actions(self) -> list[dict[str, Any]]:
        return list(self.action_catalog.get("actions", []))

    @property
    def restore_requirements(self) -> list[dict[str, Any]]:
        return list(self.restore_catalog.get("requirements", []))

    def find_control(self, control_id: str) -> dict[str, Any] | None:
        for control in self.controls:
            if control.get("control_id") == control_id:
                return control
        return None

    def by_tab(self, tab_name: str) -> list[dict[str, Any]]:
        return [control for control in self.controls if control.get("ui_tab") == tab_name]

    def by_category(self, category: str) -> list[dict[str, Any]]:
        return [control for control in self.controls if control.get("category") == category]

    def search(self, text: str = "", *, tab: str | None = None, risk: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        needle = text.strip().lower()
        rows = self.controls
        if tab and tab != "All":
            rows = [row for row in rows if row.get("ui_tab") == tab]
        if risk and risk != "All":
            rows = [row for row in rows if row.get("risk", {}).get("level") == risk]
        if status and status != "All":
            rows = [row for row in rows if row.get("status") == status]
        if needle:
            rows = [
                row
                for row in rows
                if needle in " ".join(
                    [
                        str(row.get("control_id", "")),
                        str(row.get("friendly_name", "")),
                        str(row.get("category", "")),
                        str(row.get("ui_tab", "")),
                        str(row.get("notes", "")),
                    ]
                ).lower()
            ]
        return rows

    def dry_run_preview_for(self, control: dict[str, Any]) -> str:
        future = control.get("future_apply", {})
        command = future.get("command_template") or "No command template. This control is read-only, blocked, or app-side only."
        return "\n".join(
            [
                "DRY-RUN PREVIEW ONLY",
                f"Control: {control.get('control_id')}",
                f"Risk: {control.get('risk', {}).get('level', 'Unknown')}",
                f"Command/template: {command}",
                f"Backup required: {future.get('requires_backup')}",
                f"Restore strategy: {control.get('restore', {}).get('strategy')}",
                "Phase 3 never executes this command.",
            ]
        )

    def save_app_config(self) -> Path:
        return save_json_inside_phase3(self.paths.config_dir / "app_config.json", self.app_config, self.paths)

    def save_cpu_presets(self) -> Path:
        return save_json_inside_phase3(self.paths.presets_dir / "cpu_presets.json", self.cpu_presets, self.paths)

    def save_gpu_profiles(self) -> Path:
        return save_json_inside_phase3(self.paths.presets_dir / "gpu_profiles.json", self.gpu_profiles, self.paths)

    def save_game_rules(self) -> Path:
        return save_json_inside_phase3(self.paths.presets_dir / "game_rules.json", self.game_rules, self.paths)

    def save_combined_presets(self) -> Path:
        return save_json_inside_phase3(self.paths.presets_dir / "combined_presets.json", self.combined_presets, self.paths)
