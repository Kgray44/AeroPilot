# PresentMon Candidate Notes

Phase 1 found a PresentMon candidate at:

`C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe`

The Phase 1 help and version probes did not confirm usable syntax for this candidate. Phase 2 therefore treats it as a candidate, not as the final capture tool.

Phase 2 behavior:

- List discovered candidates.
- Rank candidates by path, file existence, and optional read-only help output.
- Do not start capture sessions.
- Do not assume the AMD CNext path is the best long-term option.

Phase 3 should verify the intended PresentMon build manually and record exact capture syntax before any benchmark workflow depends on it.
