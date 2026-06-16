# PresentMon Sensor Integration

PresentMon remains opt-in in Phase 6.

The app may show:
- Candidate executable.
- Capture state.
- Output CSV path.
- Latest FPS sample.
- Latest frame-time sample.
- Latest process/runtime metadata.
- Empty CSV status.
- Errors from the adapter.

The app does not start PresentMon automatically on launch. `MainWindow.closeEvent` still calls PresentMon cleanup so a manually started capture is stopped when the app closes.
