from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.command_runner import SafeCommandRunner


class PresentMonAdapter:
    def __init__(self, runner: SafeCommandRunner, phase1_presentmon: dict[str, Any]) -> None:
        self.runner = runner
        self.phase1 = phase1_presentmon

    def candidates(self, probe_help: bool = False) -> list[dict[str, Any]]:
        raw = self.phase1.get("executable_paths") or []
        candidates = []
        for item in raw:
            path = item.get("path") if isinstance(item, dict) else str(item)
            score = self._score_path(path)
            help_status = "not probed in Phase 2"
            if probe_help:
                result = self.runner.run([path, "--help"], timeout=8, read_only=True)
                if result.exit_code == 0 and result.stdout:
                    score += 20
                    help_status = "help output succeeded"
                else:
                    help_status = f"help output not confirmed; exit={result.exit_code}"
            candidates.append(
                {
                    "path": path,
                    "exists": Path(path).exists(),
                    "score": score,
                    "help_status": help_status,
                    "phase2_capture_started": False,
                }
            )
        return sorted(candidates, key=lambda row: row["score"], reverse=True)

    def _score_path(self, path: str) -> int:
        lowered = path.lower()
        score = 0
        if "presentmon" in lowered:
            score += 30
        if "amd" in lowered or "cnext" in lowered:
            score += 5
        if "downloads" in lowered:
            score -= 5
        if Path(path).exists():
            score += 10
        return score
