from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    phase2_root: Path
    app_root: Path
    phase1_root: Path
    logs_dir: Path
    raw_outputs_dir: Path
    screenshots_dir: Path
    config_dir: Path
    presets_dir: Path
    docs_dir: Path
    restore_dir: Path

    @classmethod
    def discover(cls) -> "AppPaths":
        phase2_root = Path(__file__).resolve().parents[2]
        app_root = phase2_root.parent
        return cls(
            phase2_root=phase2_root,
            app_root=app_root,
            phase1_root=app_root / "PHASE_1_EXPLORATION",
            logs_dir=phase2_root / "logs",
            raw_outputs_dir=phase2_root / "raw_outputs",
            screenshots_dir=phase2_root / "screenshots",
            config_dir=phase2_root / "config",
            presets_dir=phase2_root / "presets",
            docs_dir=phase2_root / "docs",
            restore_dir=phase2_root / "restore",
        )

    def ensure_phase2_dirs(self) -> None:
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

    def require_inside_phase2(self, path: Path) -> Path:
        resolved = path.resolve()
        root = self.phase2_root.resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError(f"Refusing to write outside Phase 2 root: {resolved}")
        return resolved
