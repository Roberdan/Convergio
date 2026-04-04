# ADR-012: launchd with absolute paths

## Status

Accepted

## Context

macOS `launchd` runs services with a minimal `PATH` that does not include
Homebrew, Cargo, or user-installed binaries. Services that rely on `PATH`
resolution fail silently or use wrong binary versions (Learnings #19-20).

## Decision

Use absolute paths for all binaries referenced in the launchd plist file.
The plist sets a full `PATH` environment variable and references the daemon
binary by its complete filesystem path.

## Consequences

- Daemon starts correctly as a launchd service regardless of shell config.
- Binary paths must be updated in the plist when the install location changes.
- The plist includes a rebuild step after PR merge to keep the binary current.
- No dependency on the user's shell profile or PATH configuration.
