# ADR-014: Monitor with waitpid

## Status

Accepted

## Context

The agent monitor needs to detect when spawned processes terminate. Using
`kill(pid, 0)` only checks if the process exists but cannot distinguish between
a running process and a zombie process. Zombies appear alive to `kill(0)` but
are actually dead.

## Decision

Use `waitpid(pid, WNOHANG)` for process monitoring. This correctly detects
terminated processes (including zombies) and reaps them in a single call.

## Consequences

- Proper zombie detection and reaping.
- Non-blocking check via `WNOHANG` — monitor loop does not stall.
- Unix-specific code (not portable to Windows without abstraction).
- Monitor can retrieve exit status for logging and error reporting.
