# Telemetry Provider Ladder

Phase 8 uses a conservative read-only provider ladder. Sensors refresh attempts every enabled provider and records a structured ProviderStatus for each one.

1. HWiNFO shared memory
   - Preferred CPU hardware source when it is running and shared memory can be read.
   - Reports exact states: not running, shared memory unavailable/not configured, detected, failed, or ok.
   - Phase 8 probes shared memory read-only; full row parsing remains guarded until safe structure decoding is proven.

2. LibreHardwareMonitor
   - Main broad sensor source.
   - Multi-sample probe supports short read windows and stale-zero flags.
   - CPU provider health may be partial on AMD Ryzen AI hardware.
   - Valid load and VID voltage are used; invalid 0 C temperature and stale-zero 0 W/0 MHz are rejected.

3. Windows counters
   - Read-only fallback for CPU total/per-core utilization and processor frequency/performance counters.
   - Ranked below high-quality hardware providers and above stale LHM zeros.

4. WMI/CIM thermal data
   - Diagnostic only.
   - Low-confidence thermal source; not trusted as CPU die/package temperature unless clearly CPU-like.

5. ACPI thermal zones
   - Diagnostic only.
   - Low-confidence thermal fallback; generic thermal zones are not labeled CPU temperature.

6. nvidia-smi
   - Primary dGPU telemetry source for the MVP.
   - Read-only queries only.

7. PresentMon
   - FPS/frame-time source when manually started by the user.
   - No automatic capture on app launch.
   - Not-started/no-CSV is shown as idle/not started, not as a sensor failure.
