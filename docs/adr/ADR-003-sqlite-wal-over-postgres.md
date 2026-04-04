# ADR-003: SQLite + WAL over Postgres

## Status

Accepted

## Context

Convergio runs as a single-node daemon. It needs persistent storage for plans,
tasks, agents, events, and configuration. Postgres would add operational
complexity (separate process, connection management, backups) for a system that
runs on one machine.

## Decision

Use SQLite with WAL (Write-Ahead Logging) mode as the sole database engine.
Each extension owns its tables via `migrations()`. The daemon manages a single
connection pool with r2d2.

## Consequences

- Zero external dependencies for storage — no database server to install.
- Portable: the entire state is one file, easy to backup and restore.
- WAL mode allows concurrent reads during writes.
- Limited write concurrency (one writer at a time).
- No network database access — CLI must go through the daemon HTTP API.
- FTS5 available for full-text search (used by Observatory).
