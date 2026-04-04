# Convergio Decision Tree

"What tool to use when" — quick reference for common operations.

## I Need To...

### Work on Code

| Situation | Action |
|-----------|--------|
| Quick single-file fix | Direct edit (no branch needed) |
| Multi-file feature | `/solve` → `/planner` → `/execute` |
| Bug fix with tests | `/solve` → `/planner` → `/execute` |
| Existing plan task | `cvg task update <id> in_progress` → work → `submitted` |

### Manage Plans

| Situation | Action |
|-----------|--------|
| Create a plan | `/solve` → `/planner` (NEVER create without planner) |
| See plan status | `cvg plan tree <id> --human` |
| Import spec YAML | `cvg plan import <id> spec.yaml` |
| Generate spec template | `cvg plan template` |
| Check readiness | `cvg plan readiness <id>` |
| Validate wave | `cvg plan validate <id>` |
| Cancel plan | `cvg plan cancel <id> "reason"` |

### Delegate Work

| Situation | Action |
|-----------|--------|
| To remote peer (Claude) | `cvg delegation start <plan> <peer>` |
| To Copilot worker | `copilot-worker.sh <task_id> --model claude-opus-4.6` |
| Full plan auto-run | `copilot-plan-runner.sh <plan_id>` |
| Check delegation | `cvg delegation status <plan>` |
| NEVER | GitHub Issues or `@copilot` assignee |

### Manage Branches & Worktrees

| Situation | Action |
|-----------|--------|
| Wave work | `cvg wave create <plan> <wave>` |
| Feature branch | `cvg workspace create-feature <branch>` |
| Task isolation | `Task(..., isolation="worktree")` |
| NEVER | `git branch` / `git checkout -b` / `git switch -c` |
| Rebase to main | `git rebase origin/main` (NEVER `git merge main`) |

### Debug & Diagnose

| Situation | Action |
|-----------|--------|
| Plan execution tree | `cvg plan tree <id> --human` |
| Plan staleness | `cvg plan drift <id>` |
| Active agents | `cvg who agents` |
| Mesh health | `cvg mesh status` |
| Node readiness | `curl localhost:8420/api/node/readiness` |
| DB repair | `cvg ops db-repair` or restart daemon |
| Stale worktrees | `cvg reap worktrees --dry-run` |

### Access Data

| Situation | Action |
|-----------|--------|
| Query plans | `cvg plan list` (NEVER `sqlite3`) |
| Query tasks | `cvg plan tree <id>` |
| Search KB | `cvg kb search "<query>"` |
| Metrics | `cvg metrics summary` |
| Project audit | `cvg audit --project <id>` |

### Kernel & Mesh

| Situation | Action |
|-----------|--------|
| Start kernel | `cvg kernel start` |
| Set audio node | `cvg kernel here` |
| TTS | `cvg kernel say "<text>"` |
| Sync DB across nodes | `cvg mesh sync` or daemon auto-sync |
| Mesh peer status | `cvg mesh status` |
| Send heartbeat | `cvg mesh heartbeat` |

### Recovery

| Situation | Action |
|-----------|--------|
| Save checkpoint | `cvg checkpoint save <plan_id>` |
| Restore checkpoint | `cvg checkpoint restore <plan_id>` |
| After compaction | `cvg checkpoint restore` → `cvg plan execution-tree` |
| Zombie cleanup | `cvg reap worktrees && cvg reap branches && cvg reap locks` |
| Session cleanup | `session-reaper.sh --max-age 0` |

### Review & Validate

| Situation | Action |
|-----------|--------|
| Register review | `cvg review register` |
| Task validation | `cvg task validate <id> <plan>` |
| Wave validation | `cvg plan validate <plan_id>` |
| File audit | `cvg audit --path .` |
| Project audit | `cvg audit --project <id>` |

### CI & Builds

| Situation | Action |
|-----------|--------|
| Check CI | `ci-digest.sh checks <pr>` |
| Watch CI | `ci-watch.sh <branch> --repo owner/repo` |
| Run tests | `test-digest.sh` |
| Build | `build-digest.sh` |
| Full audit | `project-audit.sh --project-root $(pwd)` |

## All Commands

Run `cvg cheatsheet` for a complete list of all available commands.
