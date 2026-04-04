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

### CRITICAL: automated orchestrators produce hollow crates (Learning #14)
An automated orchestrator (phases 11-20) produced 10 crates that compile, have
green unit tests, and implement the Extension trait — but return `None` from
`routes()` and have stub handlers that do nothing. The code LOOKS complete but
is not wired to the daemon. 9/19 extensions had no HTTP routes exposed.
3 crates (org, org-package, kernel) were pure scaffolding: migrations +
`health() → Ok` with zero real logic.
**Rules**:
1. Every Extension with business logic MUST return `Some(router)` from routes()
2. Every phase MUST end with `curl` verification that new endpoints respond
3. Never trust unit tests alone — an Extension that returns None from routes()
   will pass all its internal tests but contribute nothing to the running daemon
4. The planner MUST include mandatory integration test for every phase
5. Never declare "done" without end-to-end smoke test against the running daemon

### CRITICAL: fix root causes, never shortcuts (Constitution Rule #1)
NEVER take the quick path. ALWAYS fix the root cause.
- Bug in auth? Don't add a workaround — fix the auth middleware.
- Extension returns None from routes()? Don't skip it — implement the routes.
- Script doesn't work? Don't retry the same thing — understand WHY and fix it.
- Test fails? Don't delete the test — fix the code.
- Cascading fix threshold: 3 consecutive fixes for the same issue where each
  introduces a new problem → STOP. Explain root cause, propose rebuild.
Band-aid chains are REJECTED. Workarounds become permanent. Fix it right or don't fix it.

### Full reference
All learnings, rules, architecture decisions, and phase status are in:
~/Desktop/WORKSPACE-SPLIT.md — READ IT for any non-trivial decision.
This CLAUDE.md has the critical rules that apply to every session.
WORKSPACE-SPLIT.md has the full context, history, and reasoning.

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
