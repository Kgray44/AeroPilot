# CPU Temperature Detection Debugging

Phase 6 fixes the CPU temperature parser by making selection explicit and diagnosable.

Selection rules:
- Prefer valid `Temperature` sensors from `hardware_type == Cpu`.
- Prefer names such as CPU Package, Package, Core Max, CPU Core Max, Tctl/Tdie, CPU Die, Average CPU temp, Core Average, CPU IA Cores, CPU GT Cores, P-Core Max, and E-Core Max.
- Reject values `<= 1 C` and values `>= 125 C`.
- Reject GPU, storage, and motherboard temperatures for the CPU headline.
- If no valid CPU temperature can be selected, show `CPU temp unavailable` and list accepted/rejected candidates.

Live Phase 6 probe result:
- LHM returned 139 raw sensors.
- The normalized explorer contained 149 rows after adding nvidia-smi and PresentMon-derived rows.
- The only CPU-like temperature candidate was `Core (Tctl/Tdie)` on `AMD Ryzen AI 7 350 w/ Radeon 860M`, but its value was `0 C`.
- That value is invalid by design, so CPU temperature remains unavailable until LHM exposes a valid CPU temperature.

This is a useful failure mode: the app no longer silently fails or chooses an unrelated GPU temperature.
