<!-- v1.0.0 — Merged: tool-preferences + agent-routing -->

# Tools & Routing

## Tool Mapping

| Task | Use | NOT |
|---|---|---|
| Find file | Glob | `find`/`ls` |
| Search content | Grep | `grep`/`rg` |
| Read/Edit/Create | Read/Edit/Write | `cat`/`sed`/`echo >` |
| Definition/Usages | LSP | Grep |
| Symbol search | `codegraph_search` (if `.codegraph/`) | Grep |
| Explore codebase | `Task(subagent_type='Explore')` | Multiple grep/glob |
| Audit | `project-audit.sh --project-root $(pwd)` | Manual scripts |

- ALWAYS parallelize independent tool calls
- Shell: single-quote URLs with `?`/`&`
- NEVER `!=` in SQL → use `<>`
- **NEVER pipe Bash output to `tail`/`head`/`grep`/`cat`** — PreToolUse hook blocks it. Use Grep/Read/Glob tools instead. Example: `cvg plan 2>&1 | grep import` → run `cvg plan 2>&1` alone, read output directly

## CI/Build (MANDATORY)

| AVOID | USE |
|---|---|
| `npm run lint/typecheck/build/test` | `ci-summary.sh --lint/--types/--build/--unit` |
| `gh run view --log` | `ci-digest.sh <id>` |
| `gh pr checks` | `ci-digest.sh checks <pr>` |
| `gh pr view/merge` | `cvg workspace release` / `ci-digest.sh checks <pr>` |

## Routing (NON-NEGOTIABLE)

| Trigger | Use | NOT |
|---|---|---|
| Plan (3+ tasks) | `Skill(skill="planner")` | EnterPlanMode |
| Execute | `Skill(skill="execute")` | Direct edit |
| Validate | Thor subagent | Self-declare done |

- Explore → `Explore` | Plan task → `task-executor` | Validation → `thor` | Debug → `adversarial-debugger`
- Repo knowledge: `repo-index.sh` | `agent-versions.sh [--json]`
