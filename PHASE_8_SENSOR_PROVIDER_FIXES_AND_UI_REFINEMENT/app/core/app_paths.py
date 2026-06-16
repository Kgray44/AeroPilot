from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    phase4_root: Path
    app_root: Path
    phase1_root: Path
    phase2_source_root: Path
    phase3_source_root: Path
    logs_dir: Path
    raw_outputs_dir: Path
    screenshots_dir: Path
    config_dir: Path
    presets_dir: Path
    docs_dir: Path
    restore_dir: Path

    @classmethod
    def discover(cls) -> "AppPaths":
        phase_root = Path(__file__).resolve().parents[2]
        app_root = phase_root.parent
        return cls(
            phase4_root=phase_root,
            app_root=app_root,
            phase1_root=app_root / "PHASE_1_EXPLORATION",
            phase2_source_root=app_root / "PHASE_2_APP_SKELETON_READONLY_DRYRUN",
            phase3_source_root=app_root / "PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING",
            logs_dir=phase_root / "logs",
            raw_outputs_dir=phase_root / "raw_outputs",
            screenshots_dir=phase_root / "screenshots",
            config_dir=phase_root / "config",
            presets_dir=phase_root / "presets",
            docs_dir=phase_root / "docs",
            restore_dir=phase_root / "restore",
        )

    @property
    def phase6_root(self) -> Path:
        return self.phase4_root

    @property
    def phase7_root(self) -> Path:
        return self.phase4_root

    @property
    def phase8_root(self) -> Path:
        return self.phase4_root

    @property
    def phase5_root(self) -> Path:
        return self.phase4_root

    @property
    def phase4_source_root(self) -> Path:
        return self.app_root / "PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS"

    @property
    def phase2_root(self) -> Path:
        """Compatibility alias for older copied code."""
        return self.phase4_root

    @property
    def phase3_root(self) -> Path:
        """Compatibility alias for Phase 3 code copied forward into Phase 4."""
        return self.phase4_root

    def ensure_phase4_dirs(self) -> None:
        for path in (
            self.logs_dir,
            self.raw_outputs_dir,
            self.screenshots_dir,
            self.config_dir,
            self.presets_dir,
            self.docs_dir,
            self.restore_dir,
            self.phase4_root / "backups",
            self.phase4_root / "page_photos",
            self.phase4_root / "sandbox",
        ):
            path.mkdir(parents=True, exist_ok=True)

    def ensure_phase5_dirs(self) -> None:
        self.ensure_phase4_dirs()

    def ensure_phase6_dirs(self) -> None:
        self.ensure_phase4_dirs()

    def ensure_phase7_dirs(self) -> None:
        self.ensure_phase4_dirs()

    def ensure_phase8_dirs(self) -> None:
        self.ensure_phase4_dirs()

    def ensure_phase3_dirs(self) -> None:
        self.ensure_phase4_dirs()

    def ensure_phase2_dirs(self) -> None:
        self.ensure_phase4_dirs()

    def require_inside_phase4(self, path: Path) -> Path:
        resolved = path.resolve()
        root = self.phase4_root.resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError(f"Refusing to write outside current phase root: {resolved}")
        return resolved

    def require_inside_phase5(self, path: Path) -> Path:
        return self.require_inside_phase4(path)

    def require_inside_phase6(self, path: Path) -> Path:
        return self.require_inside_phase4(path)

    def require_inside_phase7(self, path: Path) -> Path:
        return self.require_inside_phase4(path)

    def require_inside_phase8(self, path: Path) -> Path:
        return self.require_inside_phase4(path)

    def require_inside_phase3(self, path: Path) -> Path:
        return self.require_inside_phase4(path)

    def require_inside_phase2(self, path: Path) -> Path:
        return self.require_inside_phase4(path)
