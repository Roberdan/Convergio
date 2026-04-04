# Getting Started

This guide walks you through building and running the Convergio daemon locally.

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| Rust | 1.75+ | [rustup.rs](https://rustup.rs) |
| SQLite | 3.35+ (bundled) | Included via `rusqlite` with `bundled` feature |
| Git | 2.40+ | System package manager |
| curl | any | Usually pre-installed |

## Clone and build

```bash
git clone https://github.com/Roberdan/convergio.git
cd convergio/daemon
cargo build --release
```

The release binary is at `./target/release/convergio`.

## Run the daemon

```bash
./target/release/convergio
```

The daemon starts on port **8420** by default. It will:

1. Create or open the SQLite database (`convergio.db`).
2. Run all pending migrations (59+ tables across 19 extensions).
3. Register all extensions and mount their routes.
4. Start the HTTP server.

## Health check

```bash
curl http://localhost:8420/api/health
```

Expected response:

```json
{"status": "ok"}
```

For a deep health check across all 19 components:

```bash
curl http://localhost:8420/api/health/deep
```

## CLI

The `cvg` CLI communicates with the daemon via HTTP.

```bash
# Check daemon status
cvg status

# List all plans
cvg plan list

# Get details for a specific plan
cvg plan get <plan-id>
```

## Create your first plan

```bash
curl -X POST http://localhost:8420/api/plans \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Add user preferences endpoint",
    "motivation": "Users need to save display settings",
    "requester": "getting-started-guide"
  }'
```

The response includes a `plan_id`. Use it to check status:

```bash
curl http://localhost:8420/api/plans/<plan-id>
```

## Configuration

The daemon reads configuration from `convergio.toml` in the working directory.
Key sections:

| Section | Purpose |
|---------|---------|
| `[server]` | Host, port, auth mode |
| `[database]` | Path, WAL settings, pool size |
| `[inference]` | Model tiers, Ollama/OpenAI endpoints |
| `[mesh]` | Node identity, peer list, sync interval |
| `[telemetry]` | Log level, metrics export |

## Running as a macOS service

```bash
# Install the launchd plist
cp scripts/com.convergio.daemon.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.convergio.daemon.plist
```

The plist uses absolute paths (see [ADR-012](../adr/ADR-012-launchd-absolute-paths.md)).

## Next steps

- Read the [Architecture overview](architecture.md) for system design.
- Browse the [ADR collection](../adr/README.md) for key decisions.
- Check `AGENTS.md` in the repo root for contribution rules.
