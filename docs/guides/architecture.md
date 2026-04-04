# Architecture Overview

Convergio is a modular daemon (26 Rust crates) that serves as invisible
infrastructure for autonomous AI organizations.

## Three layers

```
┌─────────────────────────────────────────────────────┐
│  EXTENSIONS (pluggable, replaceable)                │
│  kernel, org, voice, billing, backup, observatory,  │
│  org-package, mcp, evidence, long-running, ...      │
├─────────────────────────────────────────────────────┤
│  PLATFORM (orchestration)                           │
│  orchestrator, agent-runtime, inference, prompts    │
├─────────────────────────────────────────────────────┤
│  INFRASTRUCTURE (core — must be perfect)            │
│  types, telemetry, db, security, ipc, mesh, server  │
└─────────────────────────────────────────────────────┘
```

**Infrastructure** provides the foundation: database, networking, security,
inter-process communication. It never contains business logic.

**Platform** coordinates work: planning, task assignment, model selection,
agent lifecycle. It depends on infrastructure but not on extensions.

**Extensions** implement business capabilities. Each is a self-contained
module that registers via the `Extension` trait. Extensions can be added
or removed without changing the core.

## Core loop

```
Goal → Org routing → Agent assignment → Model selection
  → Execution → Evidence → Thor review → Sync
```

1. A **goal** arrives (API call or user request).
2. The **orchestrator** creates a plan with waves and tasks.
3. **Thor** pre-reviews the plan before execution starts ([ADR-010]).
4. The **agent runtime** spawns agents in isolated worktrees ([ADR-005]).
5. **Inference routing** selects the appropriate model tier ([ADR-013]).
6. Agents execute, commit, push, and create PRs ([ADR-009]).
7. The **evidence gate** validates results before promotion.
8. **Thor** post-reviews completed work.
9. **Mesh sync** propagates state to peer nodes.

## Extension contract

Every module implements one trait:

```rust
pub trait Extension: Send + Sync {
    fn manifest(&self) -> ExtensionManifest;
    fn routes(&self) -> Option<Router>;
    fn migrations(&self) -> Vec<Migration>;
    fn health(&self) -> HealthStatus;
    fn metrics(&self) -> Vec<Metric>;
}
```

See [ADR-002] for the rationale. The manifest declares `provides` (capabilities
with SemVer), `requires` (dependencies), and `agent_tools` (tools callable by
AI agents).

## Dependency graph

```
types (zero deps)
  ├── telemetry
  ├── db
  ├── security
  ├── ipc ──→ db, telemetry
  ├── mesh ──→ db, security, telemetry
  ├── orchestrator ──→ db, ipc, telemetry
  ├── server ──→ collects Extension from all crates
  ├── cli ──→ types only (HTTP client, ADR-004)
  └── extensions ──→ types, db, telemetry
```

The `types` crate is the root of the dependency tree. It contains shared
data structures, the `Extension` trait, error types, and the
`DomainEventSink` trait ([ADR-008]).

## Database

SQLite with WAL mode ([ADR-003]). Each extension owns its tables via
`migrations()`. The daemon runs all migrations at startup. Current count:
59+ tables across 19 extensions.

## Key design decisions

| Decision | ADR |
|----------|-----|
| Fresh repo instead of refactoring | [ADR-001] |
| Single Extension trait | [ADR-002] |
| SQLite + WAL | [ADR-003] |
| CLI as HTTP client | [ADR-004] |
| Worktree isolation | [ADR-005] |
| No squash merge | [ADR-006] |
| Universal AGENTS.md | [ADR-007] |
| DomainEventSink via AppContext | [ADR-008] |
| Real process spawning | [ADR-009] |
| Thor pre+post review | [ADR-010] |
| Merge commit only | [ADR-011] |
| launchd absolute paths | [ADR-012] |
| Multi-tier inference | [ADR-013] |
| waitpid monitoring | [ADR-014] |

Browse all records in the [ADR directory](../adr/README.md).

[ADR-001]: ../adr/ADR-001-new-repo-over-refactoring.md
[ADR-002]: ../adr/ADR-002-extension-trait-single-contract.md
[ADR-003]: ../adr/ADR-003-sqlite-wal-over-postgres.md
[ADR-004]: ../adr/ADR-004-cli-pure-http-client.md
[ADR-005]: ../adr/ADR-005-isolated-worktrees-per-task.md
[ADR-006]: ../adr/ADR-006-no-squash-merge.md
[ADR-007]: ../adr/ADR-007-agents-md-universal.md
[ADR-008]: ../adr/ADR-008-domain-event-sink-via-appcontext.md
[ADR-009]: ../adr/ADR-009-agent-spawning-real-processes.md
[ADR-010]: ../adr/ADR-010-thor-pre-post-review.md
[ADR-011]: ../adr/ADR-011-merge-commit-only.md
[ADR-012]: ../adr/ADR-012-launchd-absolute-paths.md
[ADR-013]: ../adr/ADR-013-inference-multi-tier-routing.md
[ADR-014]: ../adr/ADR-014-monitor-waitpid.md
