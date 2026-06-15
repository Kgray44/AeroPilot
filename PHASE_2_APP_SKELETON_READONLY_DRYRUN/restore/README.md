# Restore

Phase 2 does not create restore manifests because it does not apply changes.

Phase 3 should add restore manifests before any write test:

- Export or clone the active power plan.
- Back up MSI Afterburner config and profile files.
- Record app config and preset JSON before edits.
- Verify restore immediately after any approved apply test.
