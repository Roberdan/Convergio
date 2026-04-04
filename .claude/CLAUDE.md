# Convergio — Claude Code Config

Read `AGENTS.md` in the repo root — it has ALL the rules for any LLM agent.
Read `MISSION.md` for what to do next.
Read `WORKSPACE-SPLIT.md` for full project history and detailed phase status.

## Claude-specific

- Conversation in **Italian**, code in **English**
- Use `--max-turns 50` when spawning sub-agents via daemon
- Co-Authored-By: use your model name (e.g. `Claude Opus 4.6`)
- Delegate mechanical tasks to sub-agents or Copilot to save context
- At 70-80% context: save checkpoint in WORKSPACE-SPLIT.md, tell user to start new session
