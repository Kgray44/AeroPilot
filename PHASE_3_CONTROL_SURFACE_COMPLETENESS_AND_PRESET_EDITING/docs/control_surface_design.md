# Control Surface Design

Phase 3 makes `config/control_surface_manifest.json` the source of truth for app controls. Every row has a stable `control_id`, category, UI tab and section, source reference, current read status, desired editing policy, future apply policy, restore plan, risk warning, and validation coverage.

The GUI reads this manifest instead of scattering important controls across notes or raw JSON. App-side preset files are editable, but system writes remain disabled.
