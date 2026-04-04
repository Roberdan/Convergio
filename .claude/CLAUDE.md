# Convergio — CLAUDE.md

## What is this

Convergio is a modular daemon for autonomous AI organizations.
The daemon is invisible infrastructure — like internet for AI businesses.
Value is in the organizations and agents, not the daemon itself.

## Architecture

Three layers:
- **Infrastructure** (core, must be perfect): types, telemetry, db, security, ipc, mesh, server, cli
- **Platform services** (orchestration): orchestrator, agents, inference, prompts, agent-runtime
- **Extensions** (pluggable): kernel, org, voice, http-bridge, org-package, longrunning, billing, backup, multitenancy, evidence, observatory, depgraph, mcp

Every module implements the `Extension` trait defined in `convergio-types`.
No alternative, no workaround. If it doesn't implement Extension, it doesn't exist.

## Repository layout

```
daemon/
  Cargo.toml              # workspace root (26 crates)
  src/main.rs             # binary: registers extensions, runs server
  crates/                 # 26 crates
```

## Rules

- Code and docs in **English**. Conversation in Italian.
- Max **250 lines per file**.
- CLI = pure HTTP client. Zero internal imports.
- Server = routing shell. Logic lives in crates.
- Every extension owns its DB tables via migrations().
- Conventional commits.

## Agent operational rules (MUST be in every agent prompt)

These rules come from hard-won learnings building this repo. They are non-negotiable.

### Workspace isolation
- Every task runs in its own git worktree under `.worktrees/`
- NEVER work in the main checkout at `/Users/Roberdan/GitHub/convergio`
- One worktree = one branch = one PR
- Worktree path: `.worktrees/<task-name>`

### Checklist before "done"
1. `cargo check --workspace` — whole workspace compiles
2. `cargo test -p <your-crate>` — your tests pass
3. `cargo test --workspace` — no regressions
4. **Integration smoke test** — if your crate adds routes or changes auth/config:
   rebuild daemon (`cargo build`), restart, verify `curl http://localhost:8420/api/health`
   and test YOUR new endpoints actually respond. Unit tests are NOT sufficient evidence.
5. Commit with conventional message + Co-Authored-By
6. Push and create PR with `gh pr create`
7. Check PR review comments: fix valid ones, respond to invalid ones
8. Do NOT merge until all comments resolved and CI green
9. After merge: remove worktree, delete branch, prune remote

### CRITICAL: never ship isolated crates without integration (Learning #13)
Building crates that compile and pass unit tests but don't work together is a
GRAVE PLANNING MISTAKE. Every wave must end with a working system, not just
passing tests. Auth, routing, config loading, env files — test them end-to-end.

### What NOT to do
- NEVER commit on main directly (branch protection enforced)
- NEVER create long prompts as shell arguments (use file + Read tool)
- NEVER leave stale worktrees or branches after merge
- NEVER modify files outside your task scope
- NEVER skip tests or force-push

### Prompt pattern for spawning agents
Short prompt that tells the agent to READ a file:
```
claude -p "Leggi <file> per le istruzioni. Poi inizia."
```
NEVER inline long prompts as -p arguments — they silently hang.

## Migration source

Old monolith: `/Users/Roberdan/GitHub/ConvergioPlatform/daemon/`
This repo is the clean-room destination. Move and adapt code, don't rewrite.

## Running the daemon

```bash
cd daemon
CONVERGIO_CONFIG=/path/to/config.toml cargo run
# Default port: 8420
# Health: curl http://localhost:8420/api/health
```
