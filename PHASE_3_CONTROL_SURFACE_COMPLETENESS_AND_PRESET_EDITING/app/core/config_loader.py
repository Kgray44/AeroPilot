from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .app_paths import AppPaths


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def save_json_inside_phase3(path: Path, data: Any, paths: AppPaths | None = None) -> Path:
    app_paths = paths or AppPaths.discover()
    target = app_paths.require_inside_phase3(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    return target


def save_json_inside_phase2(path: Path, data: Any, paths: AppPaths | None = None) -> Path:
    return save_json_inside_phase3(path, data, paths)


def load_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8-sig")
