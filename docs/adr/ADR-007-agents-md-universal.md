# ADR-007: AGENTS.md universal over CLAUDE.md

## Status

Accepted

## Context

The original `CLAUDE.md` configuration file was only read by Claude Code.
Other LLM agents (Copilot, Codex, Gemini, local models) ignored it entirely,
leading to inconsistent behavior across providers (Learning #20).

## Decision

Create a universal `AGENTS.md` at the repository root that contains all rules
for any LLM agent. Keep `CLAUDE.md` as a thin pointer that says "read
AGENTS.md" plus Claude-specific settings (language, model name).

## Consequences

- Provider-agnostic: any LLM agent can follow the same rules.
- Single source of truth for code style, workflow, and constraints.
- Claude-specific settings (Italian conversation, Co-Authored-By) stay in
  `.claude/CLAUDE.md`.
- New agent providers only need to be taught to read `AGENTS.md`.
