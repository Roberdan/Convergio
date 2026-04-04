# ADR-002: Extension trait as single contract

## Status

Accepted

## Context

The system needs pluggable modules (billing, observatory, voice, org management,
etc.) that can be added or removed without changing the core daemon. Multiple
contract styles were considered: service registries, plugin DLLs, microservices.

## Decision

Define one Rust trait `Extension` that every module must implement. The trait
exposes: `manifest()`, `routes()`, `migrations()`, `health()`, and `metrics()`.
The server collects all extensions at startup and wires them into the router.

## Consequences

- Zero alternative paths — every module follows the same lifecycle.
- New extensions are trivial to add: implement the trait, register in `main.rs`.
- All modules are equal citizens (no first-class vs second-class distinction).
- Tight coupling to the trait signature; changes require updating all extensions.
- HTTP bridge extensions wrap external services behind the same trait.
