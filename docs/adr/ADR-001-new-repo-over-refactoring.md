# ADR-001: New repository over refactoring

## Status

Accepted

## Context

The original Convergio repository had accumulated 845 commits, a 784 MB `.git`
directory, and significant cruft across the codebase. Refactoring in-place would
require untangling years of incremental decisions while preserving backward
compatibility with every existing script and workflow.

## Decision

Start a fresh repository with a clean workspace layout. Migrate only the
architecture decisions and proven patterns from the old codebase, not the code
itself. Build each crate from scratch following the Extension trait contract.

## Consequences

- Clean dependency graph from day one — no hidden circular imports.
- Full git history from the old repo is lost (archived separately).
- Migration scripts needed for any data carried forward.
- Every crate starts with proper tests and documentation.
