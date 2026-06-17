from __future__ import annotations

import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


@dataclass
class CommandResult:
    command: list[str]
    cwd: str | None
    read_only: bool
    dry_run: bool
    executed: bool
    exit_code: int | None
    timed_out: bool
    stdout: str
    stderr: str
    error: str | None
    started_at: str
    elapsed_seconds: float

    def to_dict(self) -> dict:
        return asdict(self)


class SafeCommandRunner:
    """Small subprocess wrapper. Phase 2 refuses non-dry-run write calls."""

    def __init__(self, log_file: Path | None = None) -> None:
        self.log_file = log_file

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: int = 15,
        read_only: bool = True,
        dry_run: bool = False,
        explanation: str = "",
    ) -> CommandResult:
        started = time.strftime("%Y-%m-%dT%H:%M:%S")
        start_time = time.monotonic()
        cmd = [str(part) for part in command]

        if dry_run or not read_only:
            result = CommandResult(
                command=cmd,
                cwd=str(cwd) if cwd else None,
                read_only=read_only,
                dry_run=True,
                executed=False,
                exit_code=None,
                timed_out=False,
                stdout="",
                stderr="",
                error=explanation or "Phase 2 dry-run preview. Command was not executed.",
                started_at=started,
                elapsed_seconds=0.0,
            )
            self._log(result)
            return result

        try:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            result = CommandResult(
                command=cmd,
                cwd=str(cwd) if cwd else None,
                read_only=True,
                dry_run=False,
                executed=True,
                exit_code=completed.returncode,
                timed_out=False,
                stdout=completed.stdout,
                stderr=completed.stderr,
                error=None,
                started_at=started,
                elapsed_seconds=round(time.monotonic() - start_time, 3),
            )
        except subprocess.TimeoutExpired as exc:
            result = CommandResult(
                command=cmd,
                cwd=str(cwd) if cwd else None,
                read_only=True,
                dry_run=False,
                executed=True,
                exit_code=None,
                timed_out=True,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                error=f"Command timed out after {timeout} seconds.",
                started_at=started,
                elapsed_seconds=round(time.monotonic() - start_time, 3),
            )
        except Exception as exc:
            result = CommandResult(
                command=cmd,
                cwd=str(cwd) if cwd else None,
                read_only=True,
                dry_run=False,
                executed=False,
                exit_code=None,
                timed_out=False,
                stdout="",
                stderr="",
                error=str(exc),
                started_at=started,
                elapsed_seconds=round(time.monotonic() - start_time, 3),
            )

        self._log(result)
        return result

    def _log(self, result: CommandResult) -> None:
        if not self.log_file:
            return
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        line = {
            "started_at": result.started_at,
            "command": result.command,
            "executed": result.executed,
            "read_only": result.read_only,
            "dry_run": result.dry_run,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "error": result.error,
        }
        import json

        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(line) + "\n")
