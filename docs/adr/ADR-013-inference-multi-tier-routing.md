# ADR-013: Inference multi-tier routing

## Status

Accepted

## Context

Different tasks require different model capabilities. A simple status check
does not need the same model as a complex architectural review. Using a single
expensive model for everything wastes budget; using only cheap models produces
poor results on hard tasks.

## Decision

Implement a 4-tier inference routing system:

| Tier | Use case | Examples |
|------|----------|---------|
| t1 | Trivial | Status formatting, template filling |
| t2 | Standard | Code generation, test writing |
| t3 | Complex | Architecture review, multi-file refactor |
| t4 | Critical | Security audit, production decisions |

A semantic classifier assigns tiers. Budget-aware downgrade falls back to a
lower tier when budget is exhausted. Local models (Ollama) serve as the
bottom-tier fallback.

## Consequences

- Cost optimization: most tasks use cheaper models.
- Local-first: Ollama handles t1/t2 without API calls.
- Graceful degradation when cloud APIs are unavailable or budget-limited.
- Classification accuracy affects quality — misrouted tasks get wrong models.
- Model configuration loaded from TOML at startup with cloud health checks.
