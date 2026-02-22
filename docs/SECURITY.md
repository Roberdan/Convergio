# Security Policy and Controls (F-26)

This document defines the practical security baseline for production deployments of Convergio.

## 1) Scope

Applies to:
- Frontend (`frontend/`) deployed on Vercel
- Backend (`backend/`) deployed on Azure Container Apps
- Data plane (Supabase Postgres + Upstash Redis)
- Integrations (Stripe, Sentry, Grafana)

## 2) Authentication and Session Flow

Convergio currently uses **session-cookie authentication** in `backend/src/api/auth.py`:
1. `POST /api/v1/auth/login` validates credentials.
2. Backend creates a DB-backed session via `create_session(...)`.
3. Backend sets `session` cookie (`HttpOnly`, `SameSite=Lax`, `Secure` in production).
4. Frontend calls `/api/v1/auth/me` to hydrate user state.
5. `POST /api/v1/auth/logout` destroys server session and clears cookie.

Current implementation details:
- Session cookie max age: 7 days.
- Passwords are stored hashed (`hash_password` / `verify_password`).
- Password change endpoint has local anti-bruteforce window (`3 attempts / 15 minutes`).

## 3) Authorization Status

Important: route registration in `backend/src/main.py` includes comments such as "no auth required" for many APIs. For production hardening:
- Enforce authentication on all non-public endpoints.
- Add role/tenant authorization checks per endpoint.
- Keep only health and explicit public endpoints unauthenticated.

## 4) Rate Limiting

Convergio supports layered rate limiting:
- **Primary**: `ProductionRateLimitMiddleware` (Redis-backed, configurable limits).
- **Compatibility**: `slowapi` handler for 429 responses.
- **Optional**: feature-flagged in-process limiter (`FEATURE_RATE_LIMIT=true`).

Recommended production defaults:
- Auth endpoints: 5 req/min per IP + account-based protections.
- General API: 100 req/min per identity.
- Admin/sensitive actions: 10 req/min.
- Return rate-limit headers and `429` with retry hints.

## 5) CORS, CSRF, and CSP

### CORS
- Configured with `CORSMiddleware` in `backend/src/main.py`.
- Allowed origins derived from `ALLOWED_ORIGINS`/`CORS_ALLOWED_ORIGINS`.
- Wildcard (`*`) is forbidden in production.
- Production allowlist should include:
  - `https://convergio.io`
  - `https://www.convergio.io`
  - `https://app.convergio.io`

### CSRF
- CSRF helpers exist in `backend/src/core/csrf.py`.
- For cookie-authenticated mutating routes (POST/PUT/PATCH/DELETE), enforce:
  - `csrf_token` cookie
  - `X-CSRF-Token` header match
- Public unauthenticated endpoints may be exempted explicitly.

### CSP
- Security headers middleware sets `Content-Security-Policy`, `X-Frame-Options`, and related headers.
- Frontend hook also sets key security headers.
- Production requirement:
  - Prefer nonce-based CSP without broad `unsafe-inline`/`unsafe-eval` for app routes.
  - Keep strict framing policy (`DENY` or controlled `SAMEORIGIN` depending on route).

## 6) Encryption in Transit and at Rest

### In transit
- Enforce HTTPS/TLS 1.2+ (prefer TLS 1.3) for:
  - Browser ↔ Vercel
  - Vercel ↔ Azure backend
  - Backend ↔ Supabase/Redis/Stripe/Sentry/Grafana
- Reject plaintext HTTP at the edge (301 redirect + HSTS).

### At rest
- Supabase Postgres data encryption is handled by provider-managed disk encryption.
- Redis provider encryption-at-rest must be enabled (provider default/plan dependent).
- Application secrets must be stored in Azure Key Vault or platform secret stores, not in code.
- API keys persisted by application logic should be encrypted before storage; Convergio includes Fernet-based key encryption in `backend/src/api/user_keys.py`.

## 7) Secret Management Requirements

- No secrets in git.
- Use Azure Container App secrets + Key Vault references.
- Rotate high-risk credentials on schedule:
  - JWT secrets
  - Stripe webhook secret
  - Sentry DSN tokens (if scoped)
  - AI provider API keys
- Minimum JWT secret length: 32+ chars (64+ recommended).

## 8) Security Contacts

For private vulnerability disclosure:
- Security team: **security@convergio.io**
- Emergency escalation: **security-emergency@convergio.io**

Include in reports:
- Affected endpoint/component
- Reproduction steps
- Impact assessment
- Suggested mitigation (optional)

## 9) Incident Handling SLA

- Initial acknowledgment: within 24h
- Critical triage: same day
- Public advisory after fix validation and coordinated disclosure

## 10) Production Security Checklist

- [ ] CORS allowlist configured with exact domains (no wildcard)
- [ ] Auth required on all non-public routes
- [ ] CSRF validation enabled for cookie-authenticated mutating endpoints
- [ ] Redis-backed rate limiting enabled
- [ ] HTTPS + HSTS enabled everywhere
- [ ] Secrets loaded from managed secret store
- [ ] Sentry enabled with PII sanitization
- [ ] Audit/review logs retained per policy
