# convergio — Meta Repo Rules

This is the **meta repository** for the Convergio ecosystem.
It contains specifications, ADRs, CI, and governance only.

## NON-NEGOTIABLE Constraints

| Rule | Reason |
|---|---|
| No source code | Source lives in component repos (ConvergioPlatform, maranello-design, etc.) |
| No build artifacts | This repo has no build step |
| No secrets or credentials | Env vars in component repos only |
| Max 250 lines/file | Platform-wide standard |
| CONSTITUTION.md is single source of truth | Never fork or override |

## Allowed Content

- `specs/` — OpenAPI and schema definitions
- `docs/adr/` — Architecture Decision Records
- `.github/workflows/` — Cross-repo CI
- `CLAUDE.md` — This file
- `CONSTITUTION.md` — Agent governance (copy of ConvergioPlatform/CONSTITUTION.md)
- `LICENSE` — MPL-2.0
- `README.md` — Ecosystem map

## ADR Convention

All ADRs follow the format defined in ADR-0300:

```
## Context
## Decision
## Rationale
## Consequences
```

Filename: `NNNN-kebab-title.md` where NNNN is sequential.

## Keeping In Sync

When `ConvergioPlatform/CONSTITUTION.md` is updated:
1. Copy the new version to this repo's `CONSTITUTION.md`
2. Update the version header in this file
3. PR with summary of changes

When daemon API changes:
1. Update `specs/openapi.yaml` version field
2. Ensure all new/changed endpoints are documented
3. Cross-repo CI will validate

## Governance

@CONSTITUTION.md
