<!-- v4.1.0 -->

# Agent Routing

Route: `claude-config/agents/` first, fallback `~/.claude/agents/`.

## Skill Routing (NON-NEGOTIABLE)

| Trigger | Use | NOT |
|---------|-----|-----|
| Plan (3+ tasks) | `Skill(skill="planner")` / `@planner` | EnterPlanMode |
| Execute | `Skill(skill="execute", args="{id}")` / `@execute {id}` | Direct edit |
| Validate | `Task(subagent_type="thor")` / `@validate` | Self-declare done |

_Why: Plan 225 — bypassing planner skips DB registration, breaking Thor tracking and wave validation._

## EnterPlanMode — Canonical Definition

**EnterPlanMode** is Claude's built-in planning UX (markdown task lists, no DB, no agent routing).

**It is ALWAYS a VIOLATION** because:
- No plan DB entry → Thor has nothing to validate against
- No wave/task tracking → progress invisible to dashboard
- No worktree isolation → risk of main branch corruption

Correct alternative: `Skill(skill="planner")` (Claude Code) or `@planner` (Copilot CLI).

Hook `guard-plan-mode` blocks EnterPlanMode at the PreToolUse level on both platforms.

## Thor — Name Aliases

Thor is the quality validation agent. Multiple names are used interchangeably:

| Name | Context |
|------|---------|
| `thor` | Subagent type: `Task(subagent_type="thor")` |
| `thor-quality-assurance-guardian` | Agent file name in `agents/` |
| `@validate` | Copilot CLI skill invocation |
| `cvg plan validate` | `cvg` CLI subcommand (plan-db.sh is DEPRECATED) |

All refer to the same role: **skeptical, independent quality gate**. Use `thor` as the canonical short name.

## Task Routing

Explore: `Explore` | Plan task: `task-executor` | Validation: `thor` (aka `thor-quality-assurance-guardian`) | Debug: `adversarial-debugger` | Parallel: Agent Teams (`TeamCreate`/`SendMessage`)

## Repo Knowledge

`repo-index.sh` | `repo-info` | `agent-versions.sh [--json|--check]` | `script-versions.sh [--json|--stale]`

