# CPU Sensor Provider Diagnostics

The live AMD Ryzen AI platform exposes useful CPU load and voltage sensors through LibreHardwareMonitor, but the current CPU temperature candidate can report 0 C and CPU power/clock sensors can report 0 W or 0 MHz.

Phase 8 treats this as a provider limitation, not as real hardware state:
- CPU load: valid when numeric and non-negative.
- CPU temperature: invalid when 0 C or outside the trusted 1-125 C range.
- CPU power: stale zero when CPU load is nonzero and power is 0 W.
- CPU clock: stale zero when CPU load is nonzero and clock is 0 MHz.
- CPU voltage: valid when in a reasonable CPU voltage range.

The CPU Diagnostics section shows valid CPU sensors, invalid sensors, stale-zero sensors, raw CPU rows, and a provider recommendation. HWiNFO shared memory is listed as a future optional provider, but Phase 8 does not read or write HWiNFO settings.
