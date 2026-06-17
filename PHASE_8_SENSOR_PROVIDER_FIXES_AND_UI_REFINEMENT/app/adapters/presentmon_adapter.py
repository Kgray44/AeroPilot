from __future__ import annotations

import csv
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from app.core.command_runner import SafeCommandRunner


class PresentMonAdapter:
    def __init__(self, runner: SafeCommandRunner, phase1_presentmon: dict[str, Any], output_dir: Path | None = None) -> None:
        self.runner = runner
        self.phase1 = phase1_presentmon
        self.output_dir = output_dir
        self._process: subprocess.Popen | None = None
        self._output_file: Path | None = None
        self._last_error: str | None = None
        self._last_command: list[str] | None = None
        self._started_at: str | None = None
        self._stopped_at: str | None = None

    def candidates(self, probe_help: bool = False) -> list[dict[str, Any]]:
        raw = self.phase1.get("executable_paths") or []
        candidates = []
        for item in raw:
            path = item.get("path") if isinstance(item, dict) else str(item)
            score = self._score_path(path)
            help_status = "not probed in app"
            if probe_help and Path(path).exists():
                result = self.runner.run([path, "--help"], timeout=8, read_only=True)
                combined = (result.stdout or "") + (result.stderr or "")
                if "output" in combined.lower() or "process" in combined.lower():
                    score += 20
                    help_status = "help output looked useful"
                else:
                    help_status = f"help output not confirmed; exit={result.exit_code}"
            candidates.append(
                {
                    "path": path,
                    "exists": Path(path).exists(),
                    "score": score,
                    "file_version": item.get("file_version") if isinstance(item, dict) else None,
                    "last_write_local": item.get("last_write_local") if isinstance(item, dict) else None,
                    "help_status": help_status,
                    "capture_started_by_app": self.is_running(),
                }
            )
        return sorted(candidates, key=lambda row: row["score"], reverse=True)

    def best_candidate(self) -> str | None:
        for row in self.candidates():
            if row.get("exists"):
                return row.get("path")
        return None

    def is_running(self) -> bool:
        return bool(self._process and self._process.poll() is None)

    def state(self) -> dict[str, Any]:
        return {
            "running": self.is_running(),
            "output_file": str(self._output_file) if self._output_file else None,
            "last_error": self._last_error,
            "last_command": self._last_command,
            "started_at": self._started_at,
            "stopped_at": self._stopped_at,
        }

    def start_capture(self, process_name: str | None = None, duration_seconds: int = 60, candidate_path: str | None = None) -> dict[str, Any]:
        if self.is_running():
            return {"ok": False, "already_running": True, "output_file": str(self._output_file), "status": "running", "error": "A PresentMon capture is already running."}
        executable = candidate_path or self.best_candidate()
        if not executable:
            return {"ok": False, "error": "No PresentMon executable candidate is available."}
        if not self.output_dir:
            return {"ok": False, "error": "No PresentMon output directory configured."}
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._output_file = self.output_dir / f"presentmon_capture_{time.strftime('%Y%m%d-%H%M%S')}.csv"
        command = [executable, "--output_file", str(self._output_file), "--timed", str(max(1, int(duration_seconds)))]
        if process_name:
            command.extend(["--process_name", process_name])
        try:
            self._process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self._last_command = command
            self._started_at = time.strftime("%Y-%m-%dT%H:%M:%S")
            self._stopped_at = None
            self._last_error = None
            payload = {"ok": True, "status": "started", "command": command, "output_file": str(self._output_file), "started_at": self._started_at}
            self._log_lifecycle(payload)
            return payload
        except Exception as exc:
            self._process = None
            self._last_error = str(exc)
            payload = {"ok": False, "error": str(exc), "command": command, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            self._log_lifecycle(payload)
            return payload

    def stop_capture(self) -> dict[str, Any]:
        if not self._process:
            payload = {"ok": True, "status": "not_running", "running": False}
            self._log_lifecycle(payload)
            return payload
        stdout = ""
        stderr = ""
        if self._process.poll() is None:
            self._process.terminate()
            try:
                stdout, stderr = self._process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                stdout, stderr = self._process.communicate(timeout=5)
        self._stopped_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        if stderr:
            self._last_error = stderr
        payload = {
            "ok": True,
            "status": "stopped",
            "running": False,
            "output_file": str(self._output_file) if self._output_file else None,
            "started_at": self._started_at,
            "stopped_at": self._stopped_at,
            "stdout": stdout,
            "stderr": stderr,
        }
        self._log_lifecycle(payload)
        return payload

    def cleanup_on_close(self) -> dict[str, Any]:
        if self.is_running():
            result = self.stop_capture()
            result["cleanup_on_close"] = True
            self._log_lifecycle(result)
            return result
        return {"ok": True, "cleanup_on_close": True, "status": "not_running"}

    def latest_reading(self) -> dict[str, Any]:
        if self._process and self._process.poll() not in (None, 0):
            try:
                _stdout, stderr = self._process.communicate(timeout=0.1)
            except Exception:
                stderr = ""
            self._last_error = stderr or self._last_error
        if not self._output_file or not self._output_file.exists():
            return {
                "ok": False,
                "running": self.is_running(),
                "status": "not_started" if not self.is_running() else "idle_no_capture",
                "error": self._last_error,
                "reason": "PresentMon capture has not been started." if not self.is_running() else "PresentMon capture is running but no CSV has been produced yet.",
                "output_file": str(self._output_file) if self._output_file else None,
            }
        rows = self._read_recent_rows(self._output_file)
        if not rows:
            return {"ok": False, "running": self.is_running(), "status": "idle_no_capture", "reason": "PresentMon CSV exists but has no data rows yet.", "empty_csv": True, "output_file": str(self._output_file)}
        frame_ms_values = [self._frame_ms(row) for row in rows]
        frame_ms_values = [value for value in frame_ms_values if value and value > 0]
        latest = rows[-1]
        avg_ms = sum(frame_ms_values) / len(frame_ms_values) if frame_ms_values else None
        fps = (1000.0 / avg_ms) if avg_ms else None
        return {
            "ok": True,
            "running": self.is_running(),
            "output_file": str(self._output_file),
            "row_count_sampled": len(rows),
            "fps_average_sample": round(fps, 1) if fps else None,
            "frametime_ms_average_sample": round(avg_ms, 2) if avg_ms else None,
            "latest_process": latest.get("ProcessName") or latest.get("Application") or latest.get("Process"),
            "latest_runtime": latest.get("Runtime") or latest.get("PresentRuntime"),
        }

    def headline(self) -> str:
        reading = self.latest_reading()
        if reading.get("ok") and reading.get("fps_average_sample"):
            return f"FPS {reading.get('fps_average_sample')}"
        if self.is_running():
            return "FPS collecting"
        return "FPS idle"

    def _read_recent_rows(self, path: Path, limit: int = 240) -> list[dict[str, str]]:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
        except UnicodeDecodeError:
            with path.open("r", encoding="utf-16", newline="") as handle:
                rows = list(csv.DictReader(handle))
        return rows[-limit:]

    def _frame_ms(self, row: dict[str, str]) -> float | None:
        for key in ("msBetweenPresents", "MsBetweenPresents", "msInPresentAPI", "FrameTime", "FrameTimeMs"):
            value = row.get(key)
            if value in (None, ""):
                continue
            try:
                return float(value)
            except ValueError:
                continue
        return None

    def _score_path(self, path: str) -> int:
        lowered = path.lower()
        score = 0
        if "presentmon" in lowered:
            score += 30
        if "capframex" in lowered or "frameview" in lowered:
            score += 15
        if "amd" in lowered or "cnext" in lowered:
            score -= 3
        if "downloads" in lowered:
            score -= 5
        if Path(path).exists():
            score += 10
        return score

    def _log_lifecycle(self, payload: dict[str, Any]) -> None:
        if not self.output_dir:
            return
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            payload = dict(payload)
            payload.setdefault("logged_at", time.strftime("%Y-%m-%dT%H:%M:%S"))
            with (self.output_dir / "presentmon_lifecycle.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")
        except Exception:
            pass
