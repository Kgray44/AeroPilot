from __future__ import annotations

from app.core.app_paths import AppPaths
from app.core.control_surface import ControlSurface


def main() -> int:
    paths = AppPaths.discover()
    assert paths.phase4_root.name == "PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS"
    assert paths.phase3_source_root.name == "PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING"
    surface = ControlSurface.load(paths)
    assert len(surface.controls) >= 100
    assert surface.find_control("cpu.boost.mode") is not None
    print("phase4 import check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
