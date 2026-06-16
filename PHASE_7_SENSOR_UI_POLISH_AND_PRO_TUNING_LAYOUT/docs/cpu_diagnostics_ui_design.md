# CPU Diagnostics UI Design

Phase 7 keeps CPU temperature diagnosis visible and explicit.

The diagnostics section includes:

- A summary card with selected status, temperature sensor counts, CPU hardware temperature sensor counts, and summary text.
- A warning card when no CPU temperature is selected.
- Accepted CPU temperature candidates.
- Rejected candidates grouped by reason.
- Raw CPU sensors.

Current live result:

- CPU temperature is unavailable.
- LHM returns CPU-like sensor `Core (Tctl/Tdie)`.
- That value reports `0.0 C`.
- The normalizer rejects that as invalid because valid CPU temperature must be greater than 1 C and less than 125 C.
- The app shows the explanation instead of silently failing.
