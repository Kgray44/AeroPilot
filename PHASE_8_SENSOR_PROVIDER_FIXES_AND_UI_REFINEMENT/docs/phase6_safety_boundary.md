# Phase 6 Safety Boundary

Phase 6 is telemetry and UI only.

Allowed work:
- Read LibreHardwareMonitor, nvidia-smi, and PresentMon status/output.
- Normalize and display sensor data.
- Save app-side sensor favorites in `config/sensor_favorites.json`.
- Capture app screenshots in `page_photos`.
- Run validation and read-only probes.

Still blocked:
- MSI Afterburner profile launches.
- NVIDIA clock, power-limit, persistence, or driver writes.
- Fan writes, embedded-controller writes, and service control.
- Startup entries, scheduled tasks, and registry writes.
- Automatic game-triggered preset apply.
- Automatic CPU/GPU tuning apply.
- Automatic PresentMon capture on app launch.

Apply gates remain inherited from Phase 5 and are not expanded in Phase 6.
