# Sensors UI Refinement

Phase 8 keeps the Phase 7 professional card layout and refines the sensor story.

Changes:
- CPU hero card can use CPU load as the primary value when temperature is invalid.
- CPU chips now show Temp unavailable, Power unavailable, Clock unavailable, and VID voltage when applicable.
- Provider health appears as compact status pills instead of long error text.
- PresentMon idle/no CSV is shown as idle, not as a scary error.
- Raw sensor explorer includes Validity, Validity reason, Provider, and Subcategory.
- CPU Diagnostics has a clear provider summary and export button for app-side JSON diagnostics.

The page remains telemetry-only. No tuning writes are exposed from the Sensors tab.
