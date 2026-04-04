# Convergio Platform — Complete Capability Reference

> Single source of truth for what Convergio can do. Load this in every agent session.
> Updated: 1 Aprile 2026 | v20.4.0

## Core Architecture

| Component | Location | Purpose |
|-----------|----------|---------|
| Daemon (Rust) | daemon/ | Control plane: HTTP API (:8420), mesh, IPC, kernel |
| Kernel | daemon/src/kernel/ | Jarvis — Local LLM (Qwen 7B), monitor, verify, recover, TTS, Telegram |
| MCP Server | daemon/src/mcp_server/ | Expose daemon as MCP tools for any LLM client |
| Evolution Engine | evolution/ | Self-improvement: observe → measure → propose → experiment |
| CLI | `cvg` | All operations: plans, tasks, waves, agents, mesh, kernel |
| Web UI | convergio-web (separate repo) | Next.js 15 + Tauri 2.0 dashboard |
| Design System | convergio-design (separate repo) | Maranello Luce DS, 5 themes, WCAG 2.2 AA |

## What Convergio CAN Do

### Plan Management
- `cvg plan create/list/show/start/complete/cancel`
- `cvg plan import <id> spec.yaml` — import from YAML spec (detailed error messages)
- `cvg plan template` — generate example spec YAML with all supported fields
- `cvg plan tree <id>` — execution tree (alias: `execution-tree`)
- `cvg plan validate <id>` — Thor wave-level validation
- `cvg plan readiness <id>` — pre-execution checks
- `cvg checkpoint save/restore <id>` — fault tolerance

### Task Execution
- `cvg task update <id> <status>` — pending/in_progress/submitted/done
- `cvg task validate <id> <plan>` — individual task validation
- Kernel verify gate: blocks "done" without evidence (tests pass, build green, files exist)

### Agent Orchestration (89 agents)
- `cvg agent start/complete "<name>"` — register/deregister
- `cvg who agents` — list active agents across mesh
- Ali (Opus) — chief of staff, planning, complex reasoning
- Thor — quality gates, validation
- Domain specialists: baccio (arch), dario (debug), marco (devops), etc.

### Mesh / Swarm (P2P multi-node)
- `cvg mesh status` — peer topology
- `cvg mesh sync` — force sync
- Multi-transport: Tailscale, SSH, LAN mDNS, HTTP
- HMAC-SHA256 auth, CRDT sync
- `scripts/mesh/deploy-node.sh <node> --kernel` — one-command deploy
- `cvg mesh sync` — daemon-managed DB replication

### Jarvis — Kernel (Local LLM on M1 Pro)
- `cvg kernel status/start/stop/logs/test/here/say`
- Qwen 2.5 7B — context-stuffed intelligent answers
- Monitor loop (30s) — health, stall detection, rate limits
- Verify gate — evidence check before task completion
- Recover — restart crashed daemons, checkpoint, notify
- TTS — Voxtral 4B neural (mlx-audio) + macOS say (Siri) fallback
- STT — whisper-rs native GGML inference (lazy model loading)
- Telegram bidirectional — text + voice, long polling
- Telegram poll health check: detect and report dead poll task
- Peer failure tracker: 3-strike consecutive failure alerts for remote nodes
- Deterministic problem triage: auto-fix daemon crash, DB lock, stale worktrees, high FD count

### Voice Engine (Plan 748, feature-gated)
- Full pipeline: Audio Capture → VAD → Wake Word → ASR → Intent → TTS
- Audio capture: `cpal` native, stereo-to-mono, linear resampling to 16kHz
- VAD: `webrtc-vad` (libwebrtc), 4 aggressiveness levels, ~10ms frame detection
- STT: `whisper-rs` (GGML), lazy model loading, Metal acceleration on Apple Silicon
- Wake word: VAD + Whisper micro-transcription for "convergio" detection
- TTS: Voxtral 4B (`mlx-community/Voxtral-4B-TTS-2603-mlx-4bit`), Italian/English voices
- Intent: rule-based classifier → cvg commands, queries, navigation, control
- State machine: Idle → Listening → WakeDetected → Processing → Speaking
- Feature flag: `cargo build --features voice` (opt-in, not default)
- Models required: `~/.cache/whisper/ggml-small.bin` (Whisper), Voxtral 4B via mlx-audio
- `mlx-audio` installed from git main (PyPI 0.4.1 lacks voxtral_tts)

### Ali Escalation / EscalateToAli
- "ali dimmi..." via Telegram/API → Claude CLI (Sonnet/Opus) subprocess
- Full system context injected automatically
- Fallback to Qwen local if Claude CLI unavailable
- Unknown problems: creates micro-plans and launches copilot-plan-runner automatically
- EscalateToAli (v20.4.0): unrecognized messages and keyword intents (report/analysis/action) escalate to Claude with full platform context — replaces AskAli

### Telegram Bot (@ConvergioBot)
- Inbound text: any message → classify intent → respond
- Inbound voice: OGG → Whisper → classify → respond text + voice
- Outbound: alerts, daily/weekly reports, plan completions
- Long polling (zero wasted requests)
- Quiet hours (23:00-07:00 CET)

### Mesh Auto-Update (v20.4.0)
- `GET /api/mesh/update-status` — version comparison across all mesh peers
- `version` + `rustc_version` fields in peer heartbeats
- Background auto-update task: 5min interval, quiet hours (23:00-07:00 CET), 30min rate limit
- Coordinator builds once, workers rsync binary from coordinator
- `start.sh` restart loop with automatic rollback on health failure
- Backup stored in `~/.convergio/bin/*.bak`

### Node Management
- `GET /api/node/readiness` — 10-check health report per node
- Role-based provisioning (kernel, executor, coordinator)
- Background DB sync via HTTP between mesh nodes (replaces rsync-only)
- Auto-rebuild: daemon rebuilds after git pull, launchd plist (5min interval)
- `caffeinate` anti-sleep for kernel node
- Secrets replication via ~/.convergio/env

### Nightly Jobs
- `GET/POST /api/nightly/jobs` — CRUD for scheduled tasks
- Model Calibration: Sunday 03:00, compare local vs cloud
- MirrorBuddy Guardian: daily 01:30
- VirtualBPM Guardian: daily 02:15

### MCP Server (convergio-mcp-server)
- Separate binary, stdio transport, JSON-RPC
- 17 tools: plans(4), agents(3), mesh(2), metrics(1), kernel(2), actions(2), control(3)
- Ring-based security (0=core, 1=trusted, 2=community, 3=sandboxed)
- Wired into Claude Code via .mcp.json
- Control tools: assign_role, interrupt_agent, reschedule_task

### Node Role Management
- `POST /api/node/assign-role` — assign kernel/executor/coordinator role
- `GET /api/node/roles` — list all node roles
- Roles stored in DB, replicated via sync

### Agent Control (kernel intervention)
- `POST /api/agent/interrupt` — stop a blocked agent via IPC bus
- `POST /api/task/reschedule` — move task to another node
- Kernel auto-detects stalls and can intervene autonomously

### Channels (OpenClaw bridge)
- 30+ platforms: WhatsApp, Telegram, Slack, Discord, etc.
- Webhook + polling support
- Channel adapters in daemon/src/channels/

### Document Ingestion
- PDF → MD, DOCX → MD, XLSX → CSV, URL, images, folders
- `cvg ingest` or daemon API with graceful fallback

### Evolution Engine
- Observe → Measure → Propose → Experiment → Validate → Learn
- A/B testing, multi-armed bandit
- Cost calibration, model routing optimization
- Proposals require human approval

### Developer Experience (v18.5.0)
- `cvg cheatsheet` / `cvg commands` — all commands grouped by domain
- `cvg api` — all daemon HTTP API endpoints with methods
- `cvg plan template` — example spec YAML with all fields + aliases
- Improved `cvg plan import` error messages: YAML location, missing keys, type hints
- `cvg plan tree` alias for `cvg plan execution-tree`
- Peer resolver: single source of truth for peer addressing (3-stage fuzzy match)
- Docs: spec-yaml-schema, mesh-delegation, delegation-guide, peer-resolver, telegram-credentials, decision-tree

## API Surface (250+ endpoints)

| Domain | GET | POST | Key endpoints |
|--------|-----|------|---------------|
| Plans | 6 | 8 | /api/plan-db/list, /json/:id, /task/update |
| Agents | 4 | 5 | /api/agents, /api/ipc/agents |
| Mesh | 8 | 4 | /api/mesh, /api/mesh/status, /api/heartbeat |
| Kernel | 3 | 5 | /api/kernel/status, /ask, /speak, /transcribe |
| Node | 1 | 0 | /api/node/readiness |
| Metrics | 4 | 1 | /api/metrics/summary, /api/tokens/daily |
| Chat | 3 | 4 | /api/chat/session, /message |
| Nightly | 3 | 3 | /api/nightly/jobs |
| Workspace | 4 | 4 | /api/workspace/create, /quality-gate |
| Memory | 2 | 2 | /api/memory/list, /stats, /gc, /delete/:file |
| Voice | 2 | 3 | /api/voice/start, /stop, /status, /wake-word |

## NON-NEGOTIABLE Rules

1. **No direct sqlite3** — use cvg CLI or daemon API only
2. **250 lines max per file** — CONSTITUTION Article V
3. **TDD mandatory** — RED → GREEN → evidence
4. **Thor validates** — executors submit, only Thor promotes to done
5. **Zero tech debt** — touch file = own all issues
6. **Verify before claim** — evidence required for every "done"
7. **Mesh delegation** — use cvg delegation for remote execution
8. **Agent identity** — cvg agent start/complete on every session

## Storage

| Path | Content |
|------|---------|
| data/dashboard.db | SQLite WAL + CRDT (plans, tasks, waves, KB) |
| ~/.claude/data/ | Symlink to data/ |
| ~/.convergio/env | Secrets (Telegram token, HF token) |
| ~/.cache/huggingface/hub/ | MLX models (Qwen, Voxtral, Whisper) |
| ~/Library/LaunchAgents/ | launchd plists (kernel, sync-db) |

## Active Repos (28 Marzo 2026)

| Repo | Status | Purpose |
|------|--------|---------|
| ConvergioPlatform | ACTIVE (SoT) | Daemon, kernel, evolution, scripts |
| convergio | ACTIVE | Meta: specs, ADR, CI, governance |
| convergio-design | ACTIVE | Design system (Maranello Luce) |
| convergio-web | ACTIVE | Web UI (Next.js + Tauri) |
| convergio-daemon | ARCHIVED | Standalone daemon (superseded) |
| convergio-app | ARCHIVED | Native macOS app (superseded) |
