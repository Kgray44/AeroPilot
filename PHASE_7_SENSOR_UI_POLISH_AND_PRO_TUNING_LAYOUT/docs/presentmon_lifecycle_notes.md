# PresentMon Lifecycle Notes

PresentMon capture is not started automatically.

Phase 5 adds lifecycle cleanup so an AeroTune-started capture is stopped when the app closes. The adapter tracks command, output CSV, start time, stop time, running/stopped state, and errors in the app logs.

The adapter refuses to start a second capture while one is already running. The Sensors page shows capture state and can display a CSV that exists but has no data rows yet without treating that as an app failure.

PresentMon remains optional. Candidate scoring and executable selection still prefer verifiable candidates, not a hard-coded path.

