# Phase 4 Safety Boundary

Phase 4 may write only Phase 4 project files, app-side JSON, backup copies under `backups/`, restore previews under `restore/`, and a temporary inactive cloned Windows power scheme used for sandbox testing.

The active power plan is never set or edited. MSI profiles are never launched. NVIDIA write commands, fan/EC writes, service control, startup entries, scheduled tasks, and registry writes remain blocked.
