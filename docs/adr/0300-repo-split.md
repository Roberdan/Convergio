# ADR 0300 — Repository Split and Ecosystem Structure

**Date**: 25 Marzo 2026
**Status**: Accepted
**Author**: Roberto D'Angelo

## Context

ConvergioPlatform grew to encompass daemon, dashboard, design system, CLI, and community
skills in a single monorepo. As the platform matured toward full native macOS (WWDC June
2026) and multi-machine swarm execution, each component needed independent release cadence,
ownership, and CI.

The meta repo `convergio` was introduced to hold cross-cutting concerns: OpenAPI spec,
ADRs, governance, and cross-repo CI — without containing source code.

## Decision

Split the ecosystem into focused repositories:

| Repo | Scope |
|---|---|
| `ConvergioPlatform` | Daemon (Rust), dashboard (JS), evolution engine (TS) |
| `maranello-design` | Design system — CSS tokens, web components |
| `convergio-community` | Shared skills, agent definitions, prompts |
| `convergio` | Meta — specs, ADRs, CI, governance (NO source code) |

## Rationale

- Independent release cadence per component. Design system ships on its own schedule.
- Reduced blast radius: a broken daemon build does not block design system PRs.
- Community contributors can fork skills without daemon access.
- Daemon stays pure Rust — no JS tooling in the same repo.
- OpenAPI spec lives in the meta repo so any consumer can depend on it without pulling
  the full daemon codebase.

## Consequences

- Cross-repo breaking changes require coordinated PRs and a version bump in `specs/openapi.yaml`.
- The `cross-repo-ci.yaml` workflow validates API compatibility on every spec change.
- CONSTITUTION.md is the single source of truth, referenced from all repos.
