# Telemetry Provider Ladder

Phase 8 uses a conservative provider ladder:

1. LibreHardwareMonitor
   - Main broad sensor source.
   - Multi-sample probe supports short read windows and stale-zero flags.
   - CPU provider health may be partial on AMD Ryzen AI hardware.

2. nvidia-smi
   - Primary dGPU telemetry source for the MVP.
   - Read-only queries only.

3. PresentMon
   - FPS/frame-time source when manually started by the user.
   - No automatic capture on app launch.

4. Windows counters
   - Read-only future fallback for CPU utilization/frequency.
   - Not polled automatically during normal UI render.

5. ACPI thermal zone
   - Diagnostic only.
   - Not trusted as CPU package temperature without manual verification.

6. HWiNFO shared memory
   - Optional future provider.
   - Phase 8 does not write HWiNFO settings or require HWiNFO.
