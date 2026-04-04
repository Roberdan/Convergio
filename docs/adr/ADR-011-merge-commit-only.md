# ADR-011: Merge commit only (enforced)

## Status

Accepted

## Context

With multiple parallel agents merging PRs, both squash merge and rebase merge
cause problems: squash loses individual commits from other branches, rebase
rewrites SHAs that other branches reference (Learnings #23-24).

## Decision

Disable squash merge and rebase merge at the GitHub repository level using:

```bash
gh api repos/OWNER/REPO -X PATCH \
  -f allow_squash_merge=false \
  -f allow_rebase_merge=false \
  -f allow_merge_commit=true
```

## Consequences

- Full history preserved for every branch and every commit.
- Merge commits appear in the log (longer but accurate history).
- Parallel agents can merge without invalidating each other's refs.
- Cannot be overridden per-PR — repository-level enforcement.
- New repositories must apply the same setting at creation time.

See also: [ADR-006](ADR-006-no-squash-merge.md) for the rationale.
