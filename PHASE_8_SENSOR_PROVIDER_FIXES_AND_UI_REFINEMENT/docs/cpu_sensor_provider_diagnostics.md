# CPU Sensor Provider Diagnostics

The live AMD Ryzen AI platform exposes useful CPU load and voltage sensors through LibreHardwareMonitor, but the current CPU temperature candidate can report 0 C and CPU power/clock sensors can report 0 W or 0 MHz.

Phase 8 treats this as a provider limitation, not as real hardware state:
- CPU load: valid when numeric and non-negative.
- CPU temperature: invalid when 0 C or outside the trusted 1-125 C range.
- CPU power: stale zero when CPU load is nonzero and power is 0 W.
- CPU clock: stale zero when CPU load is nonzero and clock is 0 MHz.
- CPU voltage: valid when in a reasonable CPU voltage range.

The CPU Diagnostics section shows valid CPU sensors, invalid sensors, stale-zero sensors, raw CPU rows, and provider recommendations. HWiNFO shared memory is probed read-only, but Phase 8 does not write HWiNFO settings and does not require HWiNFO to be installed or running.

After the provider-pipeline fix, CPU diagnostics also include:
- provider_statuses for LHM, HWiNFO, Windows counters, WMI/CIM thermal, ACPI thermal, nvidia-smi, and PresentMon.
- all_provider_sensors from every attempted provider.
- accepted_candidates and rejected_candidates.
- selected_headline_metrics.
- fallback_chain_used.
- unavailable_reasons_by_metric.

Current live behavior on this laptop:
- LibreHardwareMonitor is partial: CPU load and VID voltage are useful, while Core (Tctl/Tdie) 0 C is invalid and CPU power 0 W is stale-zero.
- Windows performance counters are available and can supply CPU clock/frequency fallback when LHM reports 0 MHz.
- HWiNFO is probed read-only. If HWiNFO is not running, the UI reports that exact state. If it is running but shared memory is unavailable, the UI reports that shared memory support is unavailable/not configured.
- WMI/CIM and ACPI thermal readings are low-confidence diagnostic fallbacks and are not labeled CPU die/package temperature unless the source is clearly CPU-like.
