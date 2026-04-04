# Convergio Constitution

Non-negotiable rules for every agent, every session, every decision.

## Rule 1: Fix root causes, never shortcuts

NEVER take the quick path. ALWAYS fix the root cause.
- Bug in auth? Fix the auth middleware, not a workaround.
- Extension returns None from routes()? Implement the routes.
- Test fails? Fix the code, not delete the test.
- 3 consecutive fixes that each introduce new problems → STOP. Explain root cause, propose rebuild.

## Rule 2: Integration test mandatory

Unit tests alone are NOT evidence. Every phase closes with a smoke test against the running system.
Learning #13-14: 793 unit tests green, daemon that didn't work.

## Rule 3: Workspace isolation

Every task in a worktree under `.worktrees/`. Never on the main checkout.
One worktree = one branch = one PR. Cleanup mandatory post-merge.

## Rule 4: Rules before agents

Rules must exist BEFORE launching agents. Never add rules to running sessions.

## Rule 5: Verifiable evidence

Never accept "done" without proof. Commit hash, curl output, test output.
Thor validates. The evidence gate rejects self-reported without verification.

## Rule 6: The planner foresees everything

Every plan includes: integration test per wave, wiring verification, final smoke test.
Never plan "create crate" without "verify the daemon serves it".

## Rule 7: Explore before building

NEVER build without first checking what exists. Read existing crates, components, old repo.
Duplicating because you didn't look is a planning failure.

## Rule 8: Never bypass without explicit user approval

No hook, rule, check, gate, or constraint can be disabled without Roberdan's approval.
If a constraint blocks work, STOP and ask. Don't decide to bypass on your own.

## Rule 9: Conserve context tokens

Context is finite. Every wasted token shortens the agent's life.
- Don't re-read files already read in this session.
- Use offset/limit for large files.
- At 70-80% context usage: save checkpoint, prepare handoff.

---

## Learnings (Appendix)

These learnings came from real incidents building this project.

1. Match commits to tasks — 38 tasks submitted without verification
2. Evidence must be verifiable, not just "posted"
3. Wave completion must trigger Thor automatically
4. Worktree isolation prevents parallel agent conflicts
5. Rules added after launch are never read by running agents
6. Closure checklist must be known before launch
7. Long prompts as shell arguments cause silent hangs — use file + Read
8. `</dev/null` with `claude -p` causes input errors
9. Heredoc with backticks causes unexpected EOF — prompts in separate files
10. Pattern: `timeout 7200 claude --dangerously-skip-permissions -p "short prompt"`
11. Orchestrator must clean worktrees after merge
12. Autonomous orchestrator works — completed 6 phases unattended
13. GRAVE: building isolated crates without integration testing
14. Automated orchestrators produce hollow crates (routes()→None, stub handlers)
