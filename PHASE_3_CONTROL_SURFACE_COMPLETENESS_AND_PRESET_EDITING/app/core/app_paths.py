from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    phase3_root: Path
    app_root: Path
    phase1_root: Path
    phase2_source_root: Path
    logs_dir: Path
    raw_outputs_dir: Path
    screenshots_dir: Path
    config_dir: Path
    presets_dir: Path
    docs_dir: Path
    restore_dir: Path

    @classmethod
    def discover(cls) -> "AppPaths":
        phase3_root = Path(__file__).resolve().parents[2]
        app_root = phase3_root.parent
        return cls(
            phase3_root=phase3_root,
            app_root=app_root,
            phase1_root=app_root / "PHASE_1_EXPLORATION",
            phase2_source_root=app_root / "PHASE_2_APP_SKELETON_READONLY_DRYRUN",
            logs_dir=phase3_root / "logs",
            raw_outputs_dir=phase3_root / "raw_outputs",
            screenshots_dir=phase3_root / "screenshots",
            config_dir=phase3_root / "config",
            presets_dir=phase3_root / "presets",
            docs_dir=phase3_root / "docs",
            restore_dir=phase3_root / "restore",
        )

    @property
    def phase2_root(self) -> Path:
        """Compatibility alias for Phase 2 code copied forward into Phase 3."""
        return self.phase3_root

    def ensure_phase3_dirs(self) -> None:
        for path in (
            self.logs_dir,
            self.raw_outputs_dir,
            self.screenshots_dir,
            self.config_dir,
            self.presets_dir,
            self.docs_dir,
            self.restore_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def ensure_phase2_dirs(self) -> None:
        self.ensure_phase3_dirs()

    def require_inside_phase3(self, path: Path) -> Path:
        resolved = path.resolve()
        root = self.phase3_root.resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError(f"Refusing to write outside Phase 3 root: {resolved}")
        return resolved

    def require_inside_phase2(self, path: Path) -> Path:
        return self.require_inside_phase3(path)
