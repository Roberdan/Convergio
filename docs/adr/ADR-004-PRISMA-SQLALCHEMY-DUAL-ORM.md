# ADR-004: Prisma + SQLAlchemy Dual ORM Strategy

## Status
Accepted

## Context
Prisma is used for schema migrations and writes. SQLAlchemy is used for read access and advanced queries.

## Decision
- Prisma manages DB schema and write operations.
- SQLAlchemy handles read-only queries and analytics.
- Both ORMs operate on the same database.

## Consequences
- Enables flexible data access.
- Requires careful schema sync.
- Both ORMs must be kept compatible.
