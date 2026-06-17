# CPU AC/DC Selector Design

The CPU Presets page now has one global power-source selector at the top: `AC` or `DC`.

Only the selected side is visible on each setting card. AC view shows only AC desired values. DC view shows only DC desired values. The preset JSON can still keep `desired_ac_value` and `desired_dc_value`, so older preset data is preserved.

When the user switches sides, AeroTune saves the visible edits into the in-memory preset before rebuilding the cards. The dry-run preview is then refreshed for the selected side only.

Each setting card shows:

- Friendly name and alias/control ID.
- Risk level.
- Enabled checkbox.
- Current readable value for the selected side when available.
- Desired value editor for the selected side.
- Difference status: matches current, would change, current unreadable, or desired not set.
- Restore source/status.
- Preview-only or apply-blocked status.

The summary row shows selected preset, selected power source, active power plan, backup gate status, sandbox test status, active CPU apply status, enabled visible settings, and visible changes.

