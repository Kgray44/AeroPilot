# Game Process Command-Line Matching

Phase 5 updates process detection to read `Win32_Process` through CIM/WMI when available.

The adapter collects:

- Process name.
- Process ID.
- Executable path when available.
- Command line when available.

Matching behavior:

- `process_names` match by exact executable name or normalized process name.
- `command_line_contains` entries are evaluated against the command line when available.
- Java targets are treated as broad and need command-line filtering.
- Steam webhelper processes are avoided as game matches.
- If command-line access is unavailable, AeroTune reports that state instead of guessing.

Game automation remains read-only. Matching a process never applies a preset in Phase 5.

