# MSI Profile Slot Mapping Notes

Phase 1 found MSI Afterburner at:

`C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe`

Phase 2 creates dry-run previews for profile slots 1 through 5 only.

Important rules:

- Do not assume Slot 1 is stock.
- Do not assume any slot is safe.
- Do not launch MSI Afterburner with profile arguments in Phase 2.
- Back up `MSIAfterburner.cfg` and the `Profiles` folder before any future profile launch test.
- Phase 3 must manually verify friendly names for each slot.

Default Phase 2 labels:

- Slot 1: Unverified
- Slot 2: Unverified
- Slot 3: Unverified
- Slot 4: Unverified
- Slot 5: Unverified
