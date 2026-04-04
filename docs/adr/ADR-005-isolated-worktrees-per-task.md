# ADR-005: Isolated worktrees per task

## Status

Accepted

## Context

Multiple AI agents working in parallel on the same repository caused file
conflicts, uncommitted changes overwriting each other, and broken builds. The
root cause was shared filesystem state (Learning #4 from project history).

## Decision

Every task gets its own git worktree under `.worktrees/`. One worktree equals
one branch equals one PR. Agents never work in the main checkout.

## Consequences

- Complete filesystem isolation between parallel tasks.
- No accidental file overwrites between agents.
- Higher disk usage (each worktree is a partial clone).
- Merge discipline required: worktrees must be cleaned up after merge.
- Branch naming convention enforced: `worktree-agent-<id>`.
