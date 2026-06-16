# Hardware Panels Design

Phase 7 replaces the Phase 6 grouped table-first overview with `HardwarePanel` cards.

Panels include:

- CPU: selected temperature status, load, power, clock, and temperature candidates.
- GPU: NVIDIA and LHM GPU readings, clocks, power, temperature, and VRAM details.
- Memory / VRAM: RAM load, VRAM used, VRAM total, and memory sensors.
- Fans / Cooling: RPM when exposed, with a clean unavailable explanation when firmware hides it.
- Storage: drive temperatures and storage sensors when exposed.
- Power / Battery: battery, AC, motherboard, and controller sensors.
- Frame / PresentMon: manual capture state and frame metrics.
- Network / Other: sensors that do not fit the primary groups.

Tables are not used as the main grouped overview. Detail rows are compact and secondary.
