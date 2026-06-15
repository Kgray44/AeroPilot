from __future__ import annotations

from app.core.app_paths import AppPaths
from app.core.control_surface import ControlSurface


def main() -> int:
    paths = AppPaths.discover()
    assert paths.phase3_root.name == "PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING"
    surface = ControlSurface.load(paths)
    assert len(surface.controls) >= 100
    assert surface.find_control("cpu.boost.mode") is not None
    assert surface.find_control("gpu.msi.profile.slot3") is not None
    assert surface.find_control("fan.ec_write.research_only") is not None
    print("phase3 import check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
