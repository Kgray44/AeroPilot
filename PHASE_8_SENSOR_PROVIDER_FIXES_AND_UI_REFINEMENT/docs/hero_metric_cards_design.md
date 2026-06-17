# Hero Metric Cards Design

Phase 7 introduces `HeroMetricCard` for the four primary telemetry groups:

- CPU.
- GPU.
- Memory / VRAM.
- Frames.

Each card separates:

- Primary value.
- Unit.
- Subtitle or explanation.
- Source badge.
- Tone.
- Progress bar.
- Mini history chart.
- Secondary metric chips.

Sensor Count and Read Status were moved out of primary cards and into status pills. This keeps the hero strip focused on readings a tuning user checks first.

The card implementation avoids showing the same text as both primary value and subtitle.
