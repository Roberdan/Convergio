# ADR-008: DomainEventSink via AppContext

## Status

Accepted

## Context

Extensions need to emit domain events (PlanCreated, TaskCompleted, etc.) without
depending directly on the IPC crate. Circular dependencies between crates would
break the clean dependency graph.

## Decision

Define a `DomainEventSink` trait in the `convergio-types` crate (which has zero
dependencies). Inject an implementation via `AppContext` at startup. Any
extension can call `ctx.event_sink().emit(event)` without importing IPC.

## Consequences

- Any extension can emit events with no direct dependency on IPC internals.
- The types crate remains dependency-free.
- Event routing is configured once at startup in `main.rs`.
- Testing is easy: inject a mock sink that collects events.
- SSE streaming consumes these events for real-time UI updates.
