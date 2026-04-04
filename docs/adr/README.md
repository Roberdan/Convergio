# Architecture Decision Records

This directory contains the ADRs for the Convergio project. Each record
documents a significant architectural decision, its context, and consequences.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [001](ADR-001-new-repo-over-refactoring.md) | New repository over refactoring | Accepted |
| [002](ADR-002-extension-trait-single-contract.md) | Extension trait as single contract | Accepted |
| [003](ADR-003-sqlite-wal-over-postgres.md) | SQLite + WAL over Postgres | Accepted |
| [004](ADR-004-cli-pure-http-client.md) | CLI as pure HTTP client | Accepted |
| [005](ADR-005-isolated-worktrees-per-task.md) | Isolated worktrees per task | Accepted |
| [006](ADR-006-no-squash-merge.md) | No squash merge | Accepted |
| [007](ADR-007-agents-md-universal.md) | AGENTS.md universal over CLAUDE.md | Accepted |
| [008](ADR-008-domain-event-sink-via-appcontext.md) | DomainEventSink via AppContext | Accepted |
| [009](ADR-009-agent-spawning-real-processes.md) | Agent spawning with real processes | Accepted |
| [010](ADR-010-thor-pre-post-review.md) | Thor pre+post review | Accepted |
| [011](ADR-011-merge-commit-only.md) | Merge commit only (enforced) | Accepted |
| [012](ADR-012-launchd-absolute-paths.md) | launchd with absolute paths | Accepted |
| [013](ADR-013-inference-multi-tier-routing.md) | Inference multi-tier routing | Accepted |
| [014](ADR-014-monitor-waitpid.md) | Monitor with waitpid | Accepted |

## Format

Each ADR follows a standard template:

```
# ADR-NNN: Title
## Status    — Accepted | Deprecated | Superseded by ADR-XXX
## Context   — Why this decision was needed
## Decision  — What was decided
## Consequences — What follows from this decision
```

## Adding a new ADR

1. Copy the template above.
2. Use the next available number.
3. Name the file `ADR-NNN-short-slug.md`.
4. Add an entry to this index.
