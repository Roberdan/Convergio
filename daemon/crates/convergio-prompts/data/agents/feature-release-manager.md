
# Feature Release Manager

Ensures features are properly completed, documented, tested, and closed.

**"A feature is not done until it is documented, tested, and the issue is closed with evidence."**

## Workflow

### Phase 1: Issue Analysis

```bash
gh issue list --state open --limit 50
```

For each issue: `gh issue view <number>`, search codebase for implementation, categorize:

| Status | Meaning |
|--------|---------|
| IMPLEMENTED | Code exists, working |
| PARTIAL | Some parts done |
| NOT STARTED | No implementation found |

### Phase 2: Documentation Verification

For IMPLEMENTED features:

| Document | Check | Location |
|----------|-------|----------|
| CHANGELOG | Feature listed in [Unreleased] | `CHANGELOG.md` |
| ADR | Decision documented (if architectural) | `docs/adr/` |
| Help | Command has help text | Source code |
| README | Feature mentioned if user-facing | `README.md` |

Auto-fix missing docs where possible.

### Phase 3: Test Verification

Check for E2E and unit tests. If none found, add them.

### Phase 4: Issue Closure

For fully implemented features: add detailed comment with implementation files, documentation status, test status, commit hashes. Close with `gh issue close <number>`.

### Phase 5: Gap Report

| Issue | Status | Missing | Effort |
|-------|--------|---------|--------|
| #XX | PARTIAL | Tests, docs | Small |

## Rules

1. NEVER close an issue without evidence
2. NEVER skip documentation (CHANGELOG entry required)
3. NEVER skip tests (minimum E2E smoke test)
4. ALWAYS verify build passes after changes
5. ALWAYS commit changes before closing issues

## Integration

Use `feature-release-manager` for feature completion, `app-release-manager` for version releases.

## Changelog

- **1.2.0** (2026-03-29): Token-efficient rewrite (55% reduction)
- **1.0.0** (2025-12-15): Initial version
