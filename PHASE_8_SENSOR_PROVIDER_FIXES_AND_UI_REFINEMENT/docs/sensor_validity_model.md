# Sensor Validity Model

Each normalized sensor now includes:
- `validity`
- `validity_reason`
- `display_status`
- `can_use_for_headline`
- `can_use_for_card`

Supported validity states:
- `valid`
- `unavailable`
- `stale_zero`
- `invalid_value`
- `unsupported`
- `hidden_by_firmware`
- `no_provider`
- `idle_no_capture`
- `not_started`
- `read_error`

Zero is not always meaningful. Load may be zero at idle, but CPU temperature at 0 C, CPU package power at 0 W while CPU load is nonzero, and CPU clocks at 0 MHz while CPU load is nonzero are not treated as headline-quality readings.
