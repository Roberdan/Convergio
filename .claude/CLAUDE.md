# Convergio — CLAUDE.md

## What is this

Convergio is a modular daemon for autonomous AI organizations.
The daemon is invisible infrastructure — like internet for AI businesses.
Value is in the organizations and agents, not the daemon itself.

## Architecture

Three layers:
- **Infrastructure** (core, must be perfect): types, telemetry, db, security, ipc, mesh, server, cli
- **Platform services** (orchestration): orchestrator, agents
- **Extensions** (pluggable): kernel, org, voice — plus HTTP-bridged external extensions

Every module implements the `Extension` trait defined in `convergio-types`.
No alternative, no workaround. If it doesn't implement Extension, it doesn't exist.

## Repository layout

```
daemon/
  Cargo.toml              # workspace root
  src/main.rs             # binary entry point
  crates/
    convergio-types/      # Extension trait, Manifest, DomainEvent, errors
    convergio-telemetry/  # tracing, metrics, health
    convergio-db/         # SQLite pool, migration runner
    convergio-security/   # auth, HMAC, audit
    convergio-ipc/        # message bus, SSE, agent registry
    convergio-mesh/       # peer discovery, sync, delegation
    convergio-server/     # Axum routing shell
    convergio-cli/        # cvg (HTTP client only)
    convergio-orchestrator/ # plans, tasks, waves, Thor
    convergio-agents/     # agent catalog, org routing
    convergio-kernel/     # Jarvis (extension)
    convergio-org/        # org chart (extension)
    convergio-voice/      # STT/TTS (extension)
```

## Dependency graph

```
types (zero deps)
  ├── telemetry -> types
  ├── db -> types
  ├── security -> types
  ├── ipc -> types, db, telemetry
  ├── mesh -> types, db, security, telemetry
  ├── orchestrator -> types, db, ipc, telemetry
  ├── server -> types, db, telemetry + all extensions
  ├── cli -> types (HTTP only)
  └── extensions -> types, db, telemetry (+ specific deps)
```

## Rules

- Code and docs in **English**. Conversation in Italian.
- Max **250 lines per file** (enforced by hook in ConvergioPlatform, best practice here).
- CLI = pure HTTP client. Zero internal imports.
- Server = routing shell. Logic lives in crates.
- Every extension owns its DB tables, registered via migrations().
- Conventional commits.

## Migration source

Old monolite: `/Users/Roberdan/GitHub/ConvergioPlatform/daemon/`
This repo is the clean-room destination. Move and adapt code, don't rewrite.

## Tracker

Progress tracked in `~/Desktop/WORKSPACE-SPLIT.md`.
