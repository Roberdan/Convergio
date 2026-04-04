# Convergio — Agent Operating Manual

This file is for ANY LLM agent working on this codebase:
Claude, Copilot, Codex, Gemini, local models, or any future system.

Read this FIRST. Then read MISSION.md for what to do. Then WORKSPACE-SPLIT.md for details.

## What is this project

Convergio is a modular daemon (26 Rust crates) for autonomous AI organizations.
The daemon is invisible infrastructure — like internet for AI businesses.

## Architecture

```
EXTENSIONS (pluggable)          ← business lives here
  kernel, org, voice, billing, backup, observatory, ...

PLATFORM (orchestration)        ← coordination
  orchestrator, agents, inference, prompts, agent-runtime

INFRASTRUCTURE (core)           ← must be perfect
  types, telemetry, db, security, ipc, mesh, server, cli
```

Every module implements the `Extension` trait. No exceptions.

## Repository layout

```
AGENTS.md                 ← YOU ARE HERE — rules for all LLM agents
MISSION.md                ← what to do (ordered steps)
WORKSPACE-SPLIT.md        ← full history, learnings, detailed phase status
CONSTITUTION.md           ← non-negotiable rules
README.md                 ← project overview
daemon/
  Cargo.toml              # workspace root (26 crates)
  src/main.rs             # binary: registers extensions, runs server
  crates/                 # all crates
scripts/                  # hooks, install scripts
claude-config/            # agent definitions, config, schemas
.claude/CLAUDE.md         # Claude Code specific (points here)
```

## Rules for ALL agents

### Code rules
- Code and docs in **English**
- Max **250 lines per file** — split if longer
- CLI = pure HTTP client, zero internal imports
- Server = routing shell, logic lives in crates
- Every extension owns its DB tables via migrations()
- Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`

### Workspace isolation
- Every task runs in its own git worktree under `.worktrees/`
- NEVER work in the main checkout
- One worktree = one branch = one PR
- After merge: remove worktree, delete branch

### Checklist before "done"
1. `cargo check --workspace` — compiles
2. `cargo test --workspace` — no regressions
3. `cargo fmt --all` — formatted
4. Integration smoke test if adding routes: `curl http://localhost:8420/api/health`
5. Commit with conventional message
6. Push and create PR
7. Do NOT merge until CI green

### The 4 questions (answer BEFORE starting any task)
1. **Who produces the input?** (which module, API, user action)
2. **Who consumes the output?** (which module, UI, another agent)
3. **How does the user see it?** (UI page, CLI command, notification)
4. **How does the system record it's done?** (DB update, event, status change)

If you can't answer all 4, the task is not ready to execute.

### Loop must be closed (Rule 10)
Every feature needs: input → processing → output → feedback → state updated → visible to user.
If the user can't see the result, it's not done.

### What NOT to do
- NEVER commit on main (hook enforced)
- NEVER ship isolated crates without integration test
- NEVER declare "done" without evidence (commit hash, curl output, test result)
- NEVER build without checking what exists first
- NEVER use workarounds — fix root causes
- NEVER re-read files already read in this session
- NEVER bypass hooks, tests, or gates without explicit user approval

### Merge protocol (CRITICAL — parallel agents)
Multiple agents may work in parallel. Merging without coordination causes:
- Conflicts that nobody resolves
- Squash merges that lose work from other branches
- WORKSPACE-SPLIT.md overwritten with stale version

**Rules:**
1. **NEVER merge with --admin if other PRs are open on the same files** — wait or coordinate
2. **Squash merge DISABLED at repo level** — only merge commits allowed (preserves history)
3. **Check open PRs before merging**: `gh pr list` — if another agent has a PR, check for conflicts first
4. **Shared files** (WORKSPACE-SPLIT.md, main.rs, Cargo.lock) require sequential merge, not parallel
5. **Code files** in different crates CAN merge in parallel (no overlap)
6. **If conflict**: pull main, rebase your branch, resolve, push —force-with-lease (not --force)
7. **The daemon should enforce this**: future Fase — POST /api/merge/request that queues merges and prevents conflicts

### Key learnings (from real incidents — read these)
- Unit tests green ≠ system works (#13). Always test E2E.
- Automated orchestrators produce hollow crates (#14). Verify routes() returns Some.
- Bottom-up building produces disconnected pieces (#15). Plan top-down.
- Agents don't update plan status (#19). The monitor MUST close the loop.
- `claude -p` with long prompts hangs (#7). Use short prompt + file.
- launchd has minimal PATH (#19-20). Use absolute paths for binaries.
- Parallel agents merging same files lose work (#23). Sequential merge for shared files.

Full learnings list in WORKSPACE-SPLIT.md.

## Running the daemon

```bash
cd daemon
cargo build --release
./target/release/convergio    # or: launchctl load com.convergio.daemon.plist
# Port: 8420
# Health: curl http://localhost:8420/api/health
# CLI: cvg status
```

## Spawning agents (the daemon does this)

```bash
curl -X POST -H "Authorization: Bearer dev-local" -H "Content-Type: application/json" \
  -d '{"agent_name":"baccio","org_id":"convergio","instructions":"...","tier":"t2","budget_usd":10}' \
  http://localhost:8420/api/agents/spawn
```

Tiers: t1=Opus (complex), t2=Sonnet (medium), t3=Haiku (simple), t4=local.

## For Copilot / Codex / other agents

If you are NOT Claude Code:
- You won't have `.claude/CLAUDE.md` loaded automatically
- Read THIS file (AGENTS.md) for all rules
- Read MISSION.md for what to do
- Read WORKSPACE-SPLIT.md for detailed status
- Same rules apply: worktrees, 250 lines, conventional commits, E2E tests
- Use `gh pr create` for PRs (not Claude-specific tooling)
