# Sensors UI Polish Design

Phase 7 changes the Sensors tab from a table-forward page into a telemetry command center.

The page hierarchy is:

- Header with refresh actions and compact status pills.
- Hero telemetry strip for CPU, GPU, Memory / VRAM, and Frames.
- Segmented navigation buttons for Overview, All Sensors, CPU Diagnostics, and Favorites.
- Hardware panels for CPU, GPU, Memory / VRAM, Fans / Cooling, Storage, Power / Battery, Frame / PresentMon, and Network / Other.
- Favorite sensors section.
- All Sensors Explorer.
- CPU Temperature Diagnostics.

Tables are still used where raw data needs table behavior, especially the All Sensors Explorer and diagnostics details. The default first viewport is now visual and glanceable.
