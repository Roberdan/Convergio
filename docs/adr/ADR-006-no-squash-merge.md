# ADR-006: No squash merge

## Status

Accepted

## Context

When multiple agents work in parallel, squash merging one branch can silently
overwrite or lose commits from other branches that were based on the same parent.
This caused lost work on at least one occasion (Learning #23).

## Decision

Disable squash merge and rebase merge at the GitHub repository level. Only merge
commits are allowed.

## Consequences

- Full commit history preserved for every branch.
- Parallel agents can merge safely without losing each other's work.
- Git log is longer with merge commits.
- Enforced at the repository settings level — cannot be bypassed per-PR.

See also: [ADR-011](ADR-011-merge-commit-only.md) for enforcement details.
