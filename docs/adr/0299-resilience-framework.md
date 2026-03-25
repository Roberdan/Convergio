# ADR 0299 — Resilience Framework

**Date**: 25 Marzo 2026
**Status**: Accepted
**Author**: Roberto D'Angelo

## Context

Early daemon deployments experienced silent failures: zombie processes, stale DB locks,
and mesh nodes that appeared online but were unresponsive. The root cause was lack of
circuit breakers and no structured recovery path. Inspired by HPC distributed systems
fault tolerance, a resilience framework was designed as a first-class platform concern.

## Decision

Adopt a mandatory resilience framework for all platform components, codified in
CONSTITUTION.md Article XI:

| Requirement | Implementation |
|---|---|
| Self-recovery | Every component handles ANY failure and restores state |
| Circuit breakers | All external boundaries: APIs, mesh nodes, DB connections |
| Retry + backoff | Exponential backoff for transient failures; max retries enforced |
| Checkpoint/restart | Long-running ops snapshot state; restart without data loss |
| Graceful degradation | Partial failure != total failure; surface degraded mode explicitly |
| Health monitoring | Every component exposes `/health` or equivalent status endpoint |
| Zero zombies | Auto-reap stale processes, worktrees, connections on detection |

## Rationale

- Mesh nodes on different machines can have network partitions. Without circuit breakers,
  a slow node would block the coordinator indefinitely.
- Agent tasks can be interrupted mid-execution. Checkpointing ensures resumability without
  data loss or duplicate work.
- Graceful degradation allows the dashboard to remain usable even when the mesh is offline.
- `/api/health` and `/api/health/deep` provide structured health signals for external monitoring.

## Consequences

- All new daemon modules must implement the `Health` trait and register with the watchdog.
- The `watchdog` subsystem runs continuous health checks and triggers auto-recovery.
- Circuit breaker state is observable via `/api/watchdog/diagnostics`.
- Agents that fail to self-recover after 2 attempts must escalate to the human operator.
