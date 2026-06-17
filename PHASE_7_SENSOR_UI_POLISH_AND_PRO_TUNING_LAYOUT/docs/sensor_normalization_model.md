# Sensor Normalization Model

`app/core/sensor_normalizer.py` converts adapter snapshots into a single model with:

- `sources`: source status for LHM, nvidia-smi, and PresentMon.
- `headline`: selected high-value readings for status bars and overview cards.
- `cards`: UI-ready metric card data.
- `groups`: categorized rows for CPU, GPU, memory, fans, storage, network, battery/power, motherboard, frame capture, and other.
- `raw_sensors`: every normalized raw sensor row.
- `diagnostics`: classification diagnostics, including CPU temperature selection.

Each normalized sensor row includes source, hardware, hardware type, sensor type, name, value, unit, min, max, normalized category, normalized key, score/confidence, selection flags, notes, and favorite status.
