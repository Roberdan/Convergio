# Convergio Production Setup Guide (F-26)

This guide describes a practical production deployment for `convergio.io` using:
- **Supabase** (Postgres)
- **Azure Container Apps** (FastAPI backend)
- **Vercel** (SvelteKit frontend)
- **Stripe** (billing)
- **Sentry** (error monitoring)
- **Grafana** (metrics dashboards)
- **DNS** for `convergio.io`

---

## 0) Prerequisites

- GitHub repository with admin access
- Azure subscription + resource group
- Supabase project
- Vercel account + project
- Stripe account
- Sentry org/project
- Grafana Cloud account (or self-hosted Grafana)
- Domain registrar/DNS provider for `convergio.io`

---

## 1) Create and Configure Supabase

1. Create a new Supabase project in the target region.
2. In Supabase, copy the Postgres connection string.
3. Ensure SSL is enabled for database connections.
4. Create a least-privilege app user for backend runtime.
5. Set `DATABASE_URL` (and/or `POSTGRES_*`) in backend secrets.
6. Run migrations from CI/CD or a secure release runner:
   ```bash
   npm run prisma:migrate
   ```
7. Verify schema health with a smoke query.

Recommended: enable PITR/backups and retention policies in Supabase.

---

## 2) Provision Azure Container Apps for Backend

1. Create/choose Azure resources:
   - Resource Group (example: `convergio-rg`)
   - Container Apps Environment
   - Azure Container Registry (or other OCI registry)
   - Azure Key Vault
2. Build backend image and push to registry.
3. Use `deployment/azure/container-app.yaml` as reference.
4. Configure ingress:
   - External = true
   - Target port = `9000`
5. Configure health probes:
   - Liveness `/health/`
   - Readiness `/health/`
6. Configure secrets in Container Apps (prefer Key Vault references):
   - `DATABASE_URL` / `POSTGRES_URL`
   - `REDIS_URL`
   - `JWT_SECRET`
   - AI provider keys
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`
   - `SENTRY_DSN`
7. Configure environment variables:
   - `ENVIRONMENT=production`
   - `PORT=9000`
   - `CORS_ALLOWED_ORIGINS=https://convergio.io,https://www.convergio.io,https://app.convergio.io`
8. Deploy revision and validate:
   - `/health/`
   - `/metrics`

---

## 3) Configure Redis (Upstash or equivalent)

1. Create Redis instance.
2. Enable TLS client connections if provider supports dedicated TLS URL.
3. Store `REDIS_URL` in backend secret store.
4. Confirm rate limiting and cache features work in logs.

---

## 4) Configure Vercel for Frontend

1. Import `frontend/` project in Vercel.
2. Verify `vercel.json` settings:
   - `regions: ["fra1"]`
   - build command present
   - cron jobs configured
3. Set Production Environment Variables (based on `frontend/.env.production`):
   - `VITE_API_URL=https://convergio-backend-prod.eastus.azurecontainerapps.io`
   - `BACKEND_URL=https://convergio-backend-prod.eastus.azurecontainerapps.io`
4. Set Preview env values for staging backend.
5. Trigger production deployment.
6. Validate login flow and cookie forwarding (`frontend/src/hooks.server.ts`).

---

## 5) Configure Stripe Billing

1. Create Stripe products/prices for plan tiers.
2. In backend secrets, set:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`
   - publishable key where needed for frontend flows
3. In Stripe Dashboard, add webhook endpoint:
   - `https://<backend-domain>/api/v1/webhooks/stripe`
4. Subscribe to required events (e.g., checkout/session/subscription lifecycle).
5. Execute test mode checkout and portal flows.
6. Verify backend webhook signature validation succeeds.

---

## 6) Configure Sentry (Backend + Frontend)

1. Create Sentry projects for backend and frontend.
2. Backend:
   - Set `SENTRY_DSN` in Azure secrets.
   - Ensure initialization path calls `init_sentry()`.
3. Frontend:
   - Configure DSN/environment/release in Vercel env vars.
4. Confirm redaction policy:
   - Backend uses breadcrumb sanitization (`backend/src/core/sentry_config.py`).
5. Trigger controlled test errors in both apps and verify ingestion.

---

## 7) Configure Grafana Monitoring

1. Choose Grafana Cloud or self-hosted Grafana.
2. Connect Prometheus data source to backend metrics endpoint (`/metrics`).
3. Add dashboards for:
   - request latency
   - error rate
   - rate-limit hits
   - queue/dependency health
4. Configure alerts:
   - high 5xx rate
   - sustained latency regression
   - auth failure spikes
5. Route alerts to on-call channels.

---

## 8) DNS Configuration for convergio.io

Set records at your DNS provider:

- `@` (root): point to your primary web edge (depending on provider setup)
- `www`: CNAME to Vercel target
- `app`: CNAME to Vercel target (recommended app entrypoint)
- `api`: CNAME to Azure Container Apps ingress FQDN

Then:
1. Add custom domains in Vercel (`convergio.io`, `www.convergio.io`, `app.convergio.io`).
2. Add custom domain in Azure Container Apps for `api.convergio.io`.
3. Provision certificates on both platforms.
4. Enforce HTTPS redirect.
5. Verify CORS allowlist includes final domains.

---

## 9) Production Validation Checklist

- [ ] Backend `/health/` and `/metrics` reachable over HTTPS
- [ ] Frontend loads from `https://app.convergio.io`
- [ ] Auth login/logout/me flow works
- [ ] Stripe checkout + webhook roundtrip works
- [ ] Sentry receives backend + frontend events
- [ ] Grafana dashboards populated and alerts armed
- [ ] CORS, CSP, and security headers validated
- [ ] Rate limits active and returning expected headers/status
- [ ] Database backups and restore procedure tested

---

## 10) Go-Live Sequence (Recommended)

1. Deploy backend and run smoke tests.
2. Deploy frontend to production domain.
3. Enable Stripe live keys and live webhook endpoint.
4. Enable Sentry + Grafana alerting.
5. Switch DNS from maintenance/staging to production.
6. Monitor first 24 hours with elevated alert sensitivity.

