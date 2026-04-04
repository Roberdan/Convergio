# ADR-009: Agent spawning with real processes

## Status

Accepted

## Context

AI agents need to execute code changes in isolated environments. Simulating
execution or running agents in-process would limit isolation and make cleanup
unreliable.

## Decision

Spawn agents as real OS processes via fork+exec. Each agent gets its own git
worktree, runs its task, commits, pushes, and creates a PR. A monitor process
tracks heartbeats and handles timeouts.

## Consequences

- True filesystem and process isolation per agent.
- Automatic cleanup via process termination.
- Push and PR creation happen from the agent's worktree.
- Process management complexity: need to handle zombies, timeouts, crashes.
- Monitor must use `waitpid(WNOHANG)` for proper detection (see ADR-014).
