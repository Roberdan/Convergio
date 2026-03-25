# Convergio — Business OS Ecosystem

> Copyright (c) 2026 Roberto D'Angelo. MPL-2.0. Not affiliated with Microsoft.

Convergio is a distributed, agent-first Business Operating System. This meta repository
is the single source of truth for cross-repo specifications, ADRs, CI, and governance.

## Ecosystem

| Repository | Purpose | Language |
|---|---|---|
| [ConvergioPlatform](https://github.com/Roberdan/ConvergioPlatform) | Daemon (107 modules), dashboard, evolution engine, IPC mesh | Rust + JS + TypeScript |
| [maranello-design](https://github.com/Roberdan/maranello-design) | Maranello Design System — UI components and tokens | CSS + JS |
| [convergio-community](https://github.com/Roberdan/convergio-community) | Community skills, agent definitions, shared prompts | YAML + Markdown |
| [convergio](https://github.com/Roberdan/convergio) | This meta repo — specs, ADRs, cross-repo CI, governance | YAML + Markdown |

## Structure

```
specs/
  openapi.yaml          — Daemon API v18.0.0 (OpenAPI 3.1)
docs/
  adr/
    0299-resilience-framework.md
    0300-repo-split.md
.github/
  workflows/
    cross-repo-ci.yaml  — Cross-repo integration checks
CLAUDE.md               — Meta repo rules for AI agents
CONSTITUTION.md         — Agent governance (single source of truth)
LICENSE                 — MPL-2.0
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Convergio Platform                │
│  ┌──────────┐  ┌───────────┐  ┌───────────────────┐ │
│  │  Daemon  │  │ Dashboard │  │  Evolution Engine │ │
│  │  :8420   │  │  :8788   │  │    (TypeScript)   │ │
│  │  (Rust)  │  │   (JS)   │  └───────────────────┘ │
│  └────┬─────┘  └─────┬────┘                         │
│       │              │                               │
│  ┌────▼──────────────▼──────┐                        │
│  │      IPC Message Bus      │                        │
│  │   (HMAC-SHA256 signed)    │                        │
│  └──────────────┬────────────┘                        │
│                 │                                    │
│  ┌──────────────▼────────────────┐                   │
│  │    Mesh Swarm (Tailscale P2P) │                   │
│  │    Multi-node, self-healing   │                   │
│  └──────────────────────────────┘                   │
└─────────────────────────────────────────────────────┘
```

## API

The Convergio daemon exposes a REST API documented at `specs/openapi.yaml`.

- Auth: Bearer token from `~/.convergio/auth/daemon.token`
- Base URL: `http://localhost:8420`
- Version: 18.0.0

## Governance

All AI agents operating in this ecosystem are governed by `CONSTITUTION.md` (v3.0.0).
Key principles: resilience, swarm intelligence, zero tech debt, transparency.

## License

MPL-2.0. See [LICENSE](./LICENSE).
