# Phase 5 Safety Boundary

Phase 5 keeps AeroTune in a guarded foundation state. It may read system state, copy app-side files, generate backup and restore manifests, and preview future commands.

Real active CPU writes remain blocked because the active power plan export is not valid. The export attempt failed from the current non-elevated session with Windows error `0x522`: a required privilege is not held by the client.

Blocked in Phase 5:

- MSI Afterburner profile launch from AeroTune.
- NVIDIA driver writes.
- Fan and embedded-controller writes.
- Windows service control.
- Startup item and scheduled-task modification.
- Registry writes.
- Automatic game-triggered preset apply.

Allowed in Phase 5:

- Read-only power plan and CPU setting display.
- Read-only process and command-line matching.
- Read-only telemetry display.
- Preview-only power plan create/set commands.
- Preview-only guarded CPU apply and restore plans.
- PresentMon capture lifecycle cleanup when a capture was started by the user.

