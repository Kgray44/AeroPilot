# Sandbox Apply Test Design

The sandbox test duplicates the current active scheme, renames the clone, confirms the clone is not active, writes low-risk test values only to the clone GUID, verifies the clone changed, restores clone values, deletes the clone, and confirms the active GUID stayed unchanged.
