# Phase 5 Backup And Restore Notes

Phase 5 generated a new backup manifest at `backups/backup_manifest_latest.json` and a restore manifest at `restore/restore_manifest_latest.json`.

The backup manifest includes:

- Active power plan GUID/name.
- Active plan export attempt result.
- Active plan query snapshot.
- CPU readable values snapshot.
- Phase 4 sandbox status.
- Phase 4 MSI backup continuation status.
- App config and preset backup path.
- Apply gate state.

The active power plan export is not valid in this run because `powercfg /export` returned error `0x522` from a non-elevated session and produced a zero-byte `.pow` file. AeroTune records that failure and leaves real CPU apply blocked.

Restore scripts remain preview-only. They are generated under `restore/generated_scripts/` and are not run by validation or app startup.

