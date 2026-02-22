# ADR-003: Session-Based Auth with HMAC-SHA256 Signed Cookies

## Status
Accepted

## Context
We need secure user authentication for web and API access. JWT was considered.

## Decision
We use session-based authentication with HMAC-SHA256 signed cookies, not JWT.

## Rationale
- Simpler session revocation
- No token expiry issues
- Server-side control over sessions
- Security headers, CSRF, rate limiting enforced

## Enforcement
`grep -r 'jwt\|python-jose' backend/` returns 0.

---
See T3-01 to T3-05 for implementation details.