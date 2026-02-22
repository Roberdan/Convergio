# Convergio Architecture (F-26)

## 1. System Overview

Convergio is a production-oriented monorepo platform that combines a SvelteKit frontend with a FastAPI backend and managed cloud services for persistence, caching, and AI-powered processing.

At a high level:

- **Frontend (SvelteKit)** delivers the user interface, authenticated dashboards, and workflow controls.
- **Backend (FastAPI)** exposes REST APIs, coordinates business logic, and orchestrates AI-agent execution.
- **Data services** include relational persistence and operational stores.
- **AI provider integrations** support LLM-based reasoning and automation tasks.

The repository is organized as a single monorepo to keep shared contracts, deployment logic, and cross-cutting architecture decisions versioned together.

## 2. Monorepo Boundaries

The monorepo is structured around clear functional boundaries:

- `frontend/`: SvelteKit application for user-facing experiences.
- `backend/`: FastAPI services, domain logic, API contracts, and orchestration.
- `prisma/`: schema and migration artifacts for relational data models.
- `docs/`: architecture, operational, and contributor documentation.
- `tests/`: integration and system test suites spanning components.
- `deployment/` and `scripts/`: infrastructure automation and operational scripts.

This layout encourages cohesive change sets and reduces drift between app layers.

## 3. Component Diagram

```text
+---------------------+      HTTPS       +---------------------+
|  SvelteKit Frontend | ---------------> |   FastAPI Backend   |
|  (Vercel Runtime)   |                  |   (Azure Runtime)   |
+----------+----------+                  +----------+----------+
           |                                        |
           |                                        |
           v                                        v
+---------------------+                  +---------------------+
|   Auth / Session    |                  |  Business Services  |
|  (frontend + API)   |                  |  + Agent Runtime    |
+----------+----------+                  +----------+----------+
           |                                        |
           +----------------+-----------------------+
                            |
                            v
        +-------------------+-------------------+
        |   Data + Inference Infrastructure     |
        |---------------------------------------|
        | Supabase (Postgres + auth features)   |
        | Upstash (Redis queues/cache/rate)     |
        | AI Providers (LLM/embeddings APIs)    |
        +---------------------------------------+
```

Primary interaction path:

1. User interacts with SvelteKit UI.
2. UI calls FastAPI endpoints with auth context.
3. FastAPI reads/writes persisted state and queue metadata.
4. FastAPI invokes AI providers when orchestration steps require model inference.
5. Results are normalized and returned to the UI.

## 4. Deployment Topology

Convergio uses a distributed managed-cloud topology:

- **Vercel** hosts the SvelteKit frontend (edge-capable web delivery).
- **Azure** hosts FastAPI services and backend compute workloads.
- **Supabase** provides managed Postgres and related platform capabilities.
- **Upstash** provides serverless Redis for caching, rate limiting, and lightweight queues.

### Runtime split

- **Presentation tier**: Vercel (frontend rendering and static assets).
- **Application tier**: Azure (API, orchestration, worker-style execution).
- **Data tier**: Supabase Postgres (+ optional object facilities).
- **Low-latency state tier**: Upstash Redis.
- **Inference tier**: External AI providers accessed from backend.

This separation improves scalability, blast-radius control, and independent release cadence.

## 5. Data Flow

### Request-response flow

1. Client requests route/page from SvelteKit.
2. Frontend acquires/forwards identity and session token.
3. Frontend sends API request to FastAPI.
4. FastAPI validates identity and authorization.
5. FastAPI executes domain logic and reads/writes Supabase Postgres.
6. FastAPI consults Upstash for cache/rate/queue semantics.
7. If needed, FastAPI calls AI providers and records prompts/results metadata.
8. FastAPI returns normalized response to frontend.
9. Frontend updates UI state.

### Asynchronous flow

1. API enqueues task metadata in Redis-backed queue patterns.
2. Worker/orchestrator pulls task and evaluates policy/guardrails.
3. Worker invokes AI provider(s) and post-processes responses.
4. Final artifacts persist to database.
5. UI fetches status or receives updates via polling/revalidation.

## 6. Security Model

Security relies on layered controls across app, data, and infrastructure.

- **Authentication**: token/session-based identity verification.
- **Authorization**: role- and tenant-aware checks in backend endpoints.
- **Transport security**: TLS for all cross-service communication.
- **Secret management**: runtime env vars and managed secret stores; no hard-coded credentials.
- **Data protection**: least-privilege DB credentials and restricted network paths.
- **Input/output hardening**: validation, schema enforcement, and safe serialization.
- **Rate limiting & abuse control**: Redis-backed throttling and request budgets.
- **Auditability**: structured logs for critical actions and orchestration decisions.

For AI interactions:

- Prompts are sanitized before provider calls.
- Provider responses are validated before persistence/use.
- Sensitive content handling follows minimization and redaction principles.

## 7. Agent Orchestration Architecture

Agent orchestration is backend-centric and policy-driven.

### Core orchestration responsibilities

- Build execution plans from user intent and system context.
- Select model/provider based on capability, latency, and cost policy.
- Maintain step state, retries, and failure recovery.
- Enforce guardrails before and after provider invocation.
- Persist outputs, traces, and status transitions for observability.

### Orchestration pipeline

1. **Task intake**: FastAPI receives an agent job request.
2. **Planning**: orchestration service decomposes work into ordered steps.
3. **Dispatch**: steps are queued and executed with idempotent semantics.
4. **Inference**: AI providers are called through controlled adapters.
5. **Validation**: outputs pass through policy and schema checks.
6. **Commit**: accepted results are written to persistent stores.
7. **Expose**: final state is returned to frontend and monitoring endpoints.

### Reliability patterns

- Retry with bounded backoff.
- Dead-letter routing for terminal failures.
- Correlation IDs for end-to-end traceability.
- Deterministic state transitions for resumability.

## 8. Observability and Operations

- Structured application logs for frontend/backend boundaries.
- Metrics around request latency, queue depth, and model invocation outcomes.
- Health checks for API and dependency readiness.
- Deployment-safe migrations and rollback-aware release process.

## 9. Architecture Decision Scope

This document captures the reference architecture for F-26 and should be updated when major changes occur in:

- frontend-backend contract shape,
- deployment topology,
- persistence or caching technology,
- or agent orchestration strategy.
