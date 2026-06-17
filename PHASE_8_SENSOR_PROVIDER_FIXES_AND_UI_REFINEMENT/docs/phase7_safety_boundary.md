# Phase 7 Safety Boundary

Phase 7 is a UI and telemetry-display phase only.

Allowed work:

- Copy Phase 6 forward into the Phase 7 folder.
- Read existing telemetry from NVIDIA, LibreHardwareMonitor, PresentMon state, and app-side JSON.
- Render normalized telemetry in a cleaner Sensors page.
- Save app-side sensor favorites and raw sensor snapshot exports inside the Phase 7 folder.
- Capture page screenshots inside `page_photos`.

Blocked work remains blocked:

- MSI Afterburner profile launches.
- NVIDIA write commands.
- Fan writes.
- Embedded controller writes.
- Service start, stop, or restart.
- Startup entry writes.
- Scheduled task creation or modification.
- Registry writes.
- Automatic game-triggered preset apply.
- Automatic CPU or GPU tuning apply.
- Automatic PresentMon capture on app launch.

Apply gates remain inherited from Phase 6. Phase 7 does not expand write capability.
