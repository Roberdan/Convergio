## Activation

Run when the user issues `/check` or asks for a session status recap.

## Phases

1. **Collect** — run `session-check.sh` via `export PATH="$HOME/.claude/scripts:$PATH" && session-check.sh 2>/dev/null || echo '{}'` and capture JSON output
2. **Git Status** — extract branch, clean/dirty state, uncommitted file count, unpushed commit count
3. **Active Plans** — list plans with status `doing` or `todo`: name, progress (done/total tasks), any stuck waves
4. **Open PRs** — list each open PR: number, title, CI status
5. **Warnings** — list every item in the `forgotten` array with `WARN:` prefix
6. **Next Steps** — list every item in `next_steps` array

## Output

- Concise Italian summary, max 15 lines total
- No tables, no headers larger than `###`
- Bold section labels: `**Git**`, `**Piani**`, `**PR**`, `**WARN**`, `**Prossimi passi**`
- If no active plans: "Nessun piano attivo"
- If no open PRs: "Nessuna PR aperta"
- If no warnings: omit the WARN section entirely
- If no next steps: "Nulla da fare"

## Guardrails

- NEVER modify any files or state during a check
- NEVER run commands other than `session-check.sh` for data collection
- NEVER emit more than 15 lines of output
- NEVER omit a section that has data
