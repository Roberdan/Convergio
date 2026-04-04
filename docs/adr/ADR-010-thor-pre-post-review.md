# ADR-010: Thor pre+post review

## Status

Accepted

## Context

Plans executed without review can waste resources on poorly defined objectives
or produce low-quality results. A validation step is needed both before
execution starts and after it completes.

## Decision

Thor acts as a challenger/reviewer with two gates:
1. **Pre-review**: validates the plan before any task starts (objective clarity,
   task decomposition, risk assessment).
2. **Post-review**: validates completed work against the original objective
   (evidence check, quality assessment).

## Consequences

- Quality gate prevents wasted execution on bad plans.
- Post-review catches issues before results reach the user.
- Thor can become a bottleneck if review is slow.
- Review failures must be handled gracefully (retry, escalate, or reject).
- Only Thor can promote task status from `submitted` to `done`.
