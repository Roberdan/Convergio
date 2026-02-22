# ADR-002: Agent Framework 1.0 Upgrade

**Status:** Accepted  
**Date:** 2026-02-15

## Context
Upgrading from agent-framework 0.x to 1.0 RC. Major API changes: AgentThread → AgentSession, new exception hierarchy, safer defaults.

## Decision
- Use AgentSession instead of AgentThread
- Adopt new exception hierarchy for error handling
- Apply safe fallback behaviors per 1.0 guidelines

## Consequences
- Improved error handling and standardized API
- Codebase is future-proofed for 1.x releases

## Enforcement
- `grep -r AgentThread .` must return 0 results
