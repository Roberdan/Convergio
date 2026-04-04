# ADR-004: CLI as pure HTTP client

## Status

Accepted

## Context

The CLI (`cvg`) needs to interact with the daemon for plan management, agent
control, status queries, and configuration. Importing daemon internals would
create tight coupling and make the CLI impossible to test independently.

## Decision

The CLI makes only HTTP calls to the daemon API. It has zero internal imports
from any daemon crate. It depends only on `convergio-types` for shared data
structures.

## Consequences

- Full decoupling: CLI and daemon can be versioned independently.
- CLI is testable without running the daemon (mock HTTP responses).
- Works across the network — CLI can target a remote daemon.
- Every feature must be exposed as an HTTP endpoint before the CLI can use it.
- 209 tests validate CLI behavior against expected HTTP contracts.
