# Sensor Command Center Design

The Phase 6 Sensors tab is organized as a command center:

1. Overview cards show headline CPU, GPU, memory, fan, FPS, frame-time, and sensor status values.
2. Mini history charts keep recent in-memory samples for important readings.
3. Grouped panels show CPU, GPU, memory, cooling, storage, other, and PresentMon readings.
4. The All Sensors explorer exposes every raw sensor row returned by LHM, nvidia-smi, and PresentMon normalization.
5. CPU Diagnostics explains which temperature sensors were accepted or rejected and why.

The raw explorer is deliberately below the graphic panels. Tables are still available for inspection, but the first view is designed for at-a-glance tuning telemetry.
