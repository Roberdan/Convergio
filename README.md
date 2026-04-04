# Convergio

A modular daemon for autonomous AI organizations.

The daemon is invisible infrastructure — like internet for AI businesses.
Value is in the organizations and agents, not the daemon itself.

## Architecture

```
EXTENSIONS (pluggable, replaceable)     ← business lives here
  kernel/Jarvis, org chart, voice, openclaw, evolution, ...

PLATFORM SERVICES (orchestrate)         ← coordination lives here
  orchestrator, agent catalog, inference routing, prompts

INFRASTRUCTURE (the daemon core)        ← must be perfect and invisible
  types, telemetry, db, security, ipc, mesh, server, cli
```

26 crates, single workspace. Every module implements the `Extension` trait.
No alternative, no workaround. If it doesn't implement Extension, it doesn't exist.

## Quick Start

```bash
cd daemon
CONVERGIO_CONFIG=~/.convergio/config.toml cargo run
# Default port: 8420
curl http://localhost:8420/api/health
```

## Repository Layout

```
daemon/
  Cargo.toml              # workspace root
  src/main.rs             # binary: registers extensions, runs server
  crates/                 # 26 crates
    convergio-types/      # Extension trait, Manifest, DomainEvent
    convergio-telemetry/  # tracing, metrics, health
    convergio-db/         # SQLite pool, migration runner
    convergio-security/   # auth, HMAC, JWT, audit
    convergio-ipc/        # message bus, SSE, agent registry
    convergio-mesh/       # peer discovery, sync, delegation
    convergio-server/     # Axum routing shell, middleware
    convergio-cli/        # cvg CLI (pure HTTP client)
    convergio-orchestrator/ # plans, tasks, waves, Thor
    convergio-agents/     # agent catalog, seed data
    convergio-inference/  # model routing, budget-aware
    convergio-prompts/    # template management, skill registry
    convergio-agent-runtime/ # spawn, scope, heartbeat, reaper
    convergio-kernel/     # Jarvis (local LLM + monitoring)
    convergio-org/        # org design, provisioning, notifications
    convergio-voice/      # STT/TTS engine
    convergio-org-package/ # org-as-package ecosystem
    convergio-http-bridge/ # external extension registration
    convergio-longrunning/ # heartbeat, checkpoint, resume
    convergio-billing/    # metering, invoices, rate cards
    convergio-backup/     # retention, snapshot, restore
    convergio-multitenancy/ # org isolation (DB, network, secret)
    convergio-evidence/   # evidence gate, workflow automation
    convergio-observatory/ # timeline, search, anomaly detection
    convergio-depgraph/   # dependency validation, OpenAPI
    convergio-mcp/        # MCP server (Claude Code bridge)
scripts/
  hooks/                  # git hooks + Claude Code hooks
```

## Key Principles

1. **Extension architecture** — everything is a plugin
2. **Single interface** — one way to register, communicate, log
3. **Every module owns its tables** — registered via trait, migrated at boot
4. **CLI = pure HTTP client** — zero internal imports
5. **Server = routing shell** — logic lives in crates
6. **Long-running first** — heartbeat, checkpoint, resume, budget tracking

## Rules

See [CONSTITUTION.md](./CONSTITUTION.md) for the non-negotiable rules.

## License

**Convergio is free. The code is open. We trust you.**

This project is released under the [Convergio Community License](./LICENSE).
The source code is public and readable, but commercial redistribution
and hosted services require explicit permission.
