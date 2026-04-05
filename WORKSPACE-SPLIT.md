# Convergio — Master Tracker

> Creato: 03 Aprile 2026 | Ultimo aggiornamento: 05 Aprile 2026 (sessione 7)
> Da monolite (129K righe) a sistema modulare espandibile.

## 1. VISION

Convergio e' una **rete di organizzazioni AI autonome che fanno business**.
Il daemon e' l'infrastruttura invisibile sotto — come internet per le aziende.
Il valore e' nelle organizzazioni e negli agenti, non nel daemon.

Il sistema deve: ricevere un problema, pianificare, eseguire, validare, completare, notificare.
Tutto visibile nella UI in tempo reale. Tutto tracciato nel DB. Tutto auditabile.

## 2. ARCHITECTURE

### Tre layer

```
EXTENSION (pluggabili, sostituibili)     <- il business vive qui
  kernel/Jarvis, org chart, voice, openclaw, evolution, ...

SERVIZI PIATTAFORMA (orchestrano)        <- il coordinamento vive qui
  orchestrator, agent catalog, inference routing

INFRASTRUTTURA (il daemon core)          <- deve essere perfetto e invisibile
  types, telemetry, db, security, ipc, mesh, server, cli
```

### Core loop
```
Goal -> Org routing -> Agent assignment -> Model selection -> Execution -> Evidence -> Thor -> Sync
```

### Extension Contract

Un solo trait `Extension`. Due modalita': Rust nativo o HTTP bridge.
Ogni modulo dichiara: `provides` (capability con SemVer), `requires` (dipendenze),
`agent_tools` (tool invocabili dagli agenti). Il sistema usa i manifest per routing,
degradazione, onboarding, LLM reasoning, SemVer check.

### Dependency graph

```
types (zero deps)
  |- telemetry, db, security
  |- ipc -> db, telemetry
  |- mesh -> db, security, telemetry
  |- orchestrator -> db, ipc, telemetry
  |- server -> raccoglie Extension da tutti
  |- cli -> types (HTTP only)
  +- extensions (kernel, org, voice) -> types, db, telemetry
```

## 3. STATO ATTUALE (05 Aprile 2026 sessione 8 — onesto)

### Numeri

| Metrica | Valore |
|---------|--------|
| Crate nel workspace | 28 |
| Extension registrate in main.rs | 21 (tutte con `routes()` -> `Some`) |
| Test passanti (`cargo test --workspace`) | 995 (verificato sessione 8) |
| Righe Rust totali | ~53.800 |
| Endpoint HTTP unici | ~160 |
| Tabelle DB (via migrations) | 61+ |
| PR mergiate | 109 |

### Cosa funziona realmente (verificato con smoke test)

- **Daemon boot**: main.rs -> pool -> migrations -> 21 extension -> routes -> serve
- **Auth**: Bearer token + dev-mode localhost bypass
- **Config hot-reload**: watcher con debounce 500ms
- **WAL checkpoint**: graceful shutdown
- **Plan CRUD**: create/list/get/start/complete/cancel/checkpoint
- **Plan protocol**: objective/motivation/requester required, validate endpoint
- **Plan lifecycle**: task submitted -> wave done -> plan done (AUTOMATICO, sessione 5)
- **Thor plan review**: pre-review required before plan start, post-review on completion
- **IPC**: agents, messages, channels, context, SSE stream
- **Mesh batch sync**: export/import via HTTP con HMAC auth + background loop
- **Extension routes**: 21/21 registrate, tutte rispondono a curl
- **SSE domain events**: PlanCreated, TaskCompleted, WaveCompleted, PlanCompleted
- **Evidence gates**: record/query/gates/preflight (column names fixed sessione 5)
- **Billing metering**: usage/invoices/rates/alerts
- **Observatory**: timeline/search/dashboard/anomaly (persiste in DB)
- **Agent spawning**: reale con monitor, worktree, push, PR automatica + auto-respawn
- **Agent context API**: per-agent live KV dal DB, seed da task/plan, CRUD endpoint
- **Agent live adaptation**: poll updates (plan/task/context/messages), sentinel files (STOP/PRIORITY_CHANGE)
- **Long-run autonomo**: auto-respawn su checkpoint, max 5 tentativi, budget propagation
- **Worktree cleanup**: auto-cleanup worktrees+branches on PlanCompleted (sessione 7)
- **Auto-learning**: key_learnings_json auto-extracted on PlanCompleted (sessione 7)
- **Inference**: HTTP (Ollama/OpenAI-compatible) + MLX subprocess diretto (sessione 8)
- **Harness engineering**: init.sh baseline, Thor separato, one-feature-at-a-time (sessione 8)
- **Depgraph**: wired in main.rs, 19 componenti, graph validation
- **Health/Metrics**: /api/health/deep (19 componenti), /api/metrics (33+ metriche)
- **launchd**: plist con PATH completo, daemon rebuild dopo PR merge
- **File transport**: rsync push/pull tra nodi via SSH (4 endpoint)
- **Node capability registry**: register/query peer capabilities con scoring (5 endpoint mesh)
- **Delegation orchestrator**: copy -> spawn -> monitor -> sync back -> DelegationCompleted event (completo)
- **Inference model config**: modelli registrati al startup da TOML config, cloud health check automatico
- **Artifact model**: upload/download non-code artifacts, multipart, evidence type artifact/document
- **E2E HTTP tests**: plan lifecycle, delegation pipeline, task CRUD (13 integration test)
- **Scheduler policy**: weighted scoring (capability, cost, load, locality), policy CRUD, decision history
- **Human approval**: approval requests, thresholds with auto-approve, review/reject flow
- **Compensation/rollback**: compensation plans, action execution, wave rollback tracking
- **Security remote**: trust levels (5 livelli), secret filtering, sandbox policies per peer
- **Evaluation framework**: plan evaluation, Thor precision/recall/F1, review outcome tracking
- **ADR documentation**: 14 ADR + getting-started + architecture guide
- **Self-build**: POST /api/build/self triggers check+test+build, deploy+rollback, history (sessione 8)

### Remaining gaps
- **Frontend**: convergio-frontend non ancora integrato (deferred)

Diagnosi sessione 8: Step 0-5 COMPLETI. 28 crate, 21 extension, 995 test, 109 PR. Sessione 8 ha completato: Fase 26 (self-build, PR #103), Fase 49 (harness, PR #107), Fase 51 (MLX backend, PR #109). In corso: benchmark MLX vs Ollama per Kernel/Jarvis.

### Workflow (12/12 step OK — COMPLETO)

## 4. FASI COMPLETATE (storia collassata)

Wave A (infra): fasi 0-6 — types, telemetry, db, security, ipc, mesh (91 test)
Wave B (orch+cli): fasi 7-8 — orchestrator, cli (249 test)
Wave C (server): fasi 9-10 — server, extensions kernel/org/voice (91 test)
Wave D (intelligence): fasi 11-14 — inference, prompts, org-package, HTTP bridge (106 test)
Wave E (runtime): fasi 15-18d — longrun, depgraph, agent runtime, MCP, billing, backup, multitenant (210 test)
Wave F (observability): fasi 19-20 — observatory, evidence gates (46 test)
Phase 21-24 (wiring): routes, stubs, E2E, plan protocol, PM endpoints (825 test)
Phase 27-29 (guardrails): hooks, skills, agent TOML, config, CONSTITUTION
Phase 32 (spawning): agent spawn, mesh sync, telegram, launchd
Step 0 (sessione 5): 32b-d lifecycle wiring, planner E2E, Thor review (#63-#69)

### Step 1: Fondamenta — DONE (sessione 6)

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 23e | DepgraphExtension wiring | #48 | Verificato: wired, routes, health, startup validation |

### Step 2: Delegation pipeline — DONE (sessione 6)

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 31 | File transport (rsync) | #75 | Push/pull via SSH, transfer tracking, 4 endpoint |
| 37b | Node capability registry | #74 | Register/query/score peer capabilities, 5 endpoint |
| 34 | Delegation orchestrator monitoring | #79 | Remote tmux monitor, sync_back, DelegationCompleted event |
| 35 | E2E integration test delegation | #80 | 4 integration test axum::oneshot |

### Step 3: Completamento — DONE (sessione 6-7)

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 36b | Inference model config | #81 | TOML config, startup registration, cloud health check |
| 39b | Artifact model + non-code | #82 | Upload/download, multipart, new evidence types |
| 40b | E2E HTTP tests | #83 | 9 plan lifecycle integration tests |
| 32e | Agent context API | #94 | Live per-agent context from DB |
| 32f | Agent live adaptation | #95 | Poll updates and sentinel files |
| 32g | Long-run autonomo | #97 | Auto-respawn on checkpoint |
| -- | Worktree cleanup | #98 | Auto-cleanup worktrees+branches on PlanCompleted |
| -- | Auto-learning extraction | #98 | Auto-generate key_learnings_json on PlanCompleted |
| -- | Frontend | -- | DEFERRED — repo separato, richiede agenti UI |

### Step 3b: Documentation — DONE (sessione 6)

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 47 | ADR + documentazione | #85 | 14 ADR, getting-started guide, architecture guide |

### Step 4: Production hardening — DONE (sessione 6)

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 41 | Artifact bundles + metadata | #86 | Bundle CRUD, mime_type, content_hash, lifecycle draft→published |
| 42 | Human-in-the-loop approval | #88 | Approval requests, thresholds, auto-approve below, review flow |
| 43 | Compensation/rollback | #87 | Compensation plans, action execution, wave rollback |
| 44 | Scheduler policy | #90 | Weighted scoring, 4 policy weights, decision history |
| 45 | Security remote execution | #89 | 5 trust levels, secret filtering, sandbox per peer |
| 46 | Evaluation framework | #91 | Plan evaluation, Thor precision/recall/F1, review outcomes |

### Step 3: Completamento (remaining) — DONE except Frontend (sessione 7)

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 32e | Agent context API | #94 | Per-agent KV dal DB, CRUD, seed da task/plan |
| 32f | Agent live adaptation | #95 | Poll updates, sentinel files, STOP detection |
| 32g | Long-run autonomo | #97 | Auto-respawn su checkpoint, max 5 tentativi, budget propagation |
| -- | Frontend | -- | DEFERRED — repo separato, richiede agenti UI |

### Step 5: Self-hosting — DONE (sessione 8)

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 26 | Self-build extension | #103 | Build/test/deploy pipeline, CLI, 5 endpoint, 15 test |

### Sessione 8 fasi completate

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 26 | Self-build extension | #103 | Build/test/deploy pipeline, CLI, 5 endpoint, 15 test |
| 49 | Harness engineering (minimal) | #107 | init.sh baseline, Thor separato, one-feature, harness.rs |
| 51 | MLX backend diretto | #109 | backend_mlx.rs subprocess, ModelProvider::Mlx, TurboQuant config |

## 5. FASI IN CORSO

Sessione 8: benchmark MLX completato, prossimo Fase 52 (Kernel/Jarvis).

## 6. FASI FUTURE (ordinate per priorita')

### Benchmark MLX sessione 8 (M1 Pro 32GB) — RISULTATI

| Modello | Task | Gen (s) | tok/s | Qualita' |
|---------|------|---------|-------|----------|
| Qwen 0.5B 4bit | classify | 0.90 | 222 | Verboso, non si ferma |
| Qwen 0.5B 4bit | code | 0.87 | 230 | Buono |
| **Qwen 7B Coder 4bit** | **classify** | **0.58** | 9 | **PERFETTO** ("domanda") |
| **Qwen 7B Coder 4bit** | **code** | **1.30** | 32 | **ECCELLENTE** (usa std::net) |
| **Qwen 7B Coder 4bit** | **reason** | **5.23** | 38 | Buono |
| Gemma 3 4B 4bit | classify | 4.21 | 48 | PESSIMO (loop infinito) |
| Gemma 3 4B 4bit | code | 2.97 | 55 | Mediocre (buggato) |

**Decisione**: Qwen 7B Coder su MLX e' il modello per Kernel/Jarvis.
Classificazione in 0.58s, codice eccellente, daemon lo tiene caldo in memoria.
Gemma 3 4B scartata (qualita' inaccettabile). Qwen 0.5B come fallback veloce.

### Fase 52: Kernel/Jarvis su M1 Pro — nodo voice/assistant

**Modello scelto**: Qwen 7B Coder 4bit su MLX (benchmark sessione 8).
Classificazione Telegram: 0.58s. Codice: 1.3s. Ragionamento: 5.2s. Gratis.

**Task**:
- [ ] Registrare M1 Pro nel node capability registry con voice/kernel/telegram
- [ ] Configurare Telegram bot token su M1 Pro (~/.convergio/env)
- [ ] Watchdog locale: Qwen 7B classifica, risponde o escala
- [ ] Telegram → kernel → risposta locale O delega a M5 Max/cloud
- [ ] Test: manda messaggio Telegram → kernel classifica → risponde

### Fase 50: Autoresearch loop — ottimizzazione continua notturna

**Task**:
- [ ] Loop controller nel daemon: scheduled task notturno (cron 02:00)
- [ ] Metrica oggettiva per tipo progetto: Rust=cargo test+bench, TS=vitest
- [ ] Registra ogni esperimento in DB (tentativo, risultato, keep/discard)
- [ ] Usa modelli LOCALI (MLX Qwen 7B), non API cloud — gratis
- [ ] Dashboard esperimenti: GET /api/autoresearch/results

### Remaining
- **Frontend**: rifare convergio-frontend (deferred, agenti via daemon)
- **48**: Node provisioning (sync config/memory/keys a nodi remoti)

### Fasi non completate (bassa priorita')
- **22**: Cutover (manuale, quando Roberto decide)
- **25**: Script->daemon (deprecare script bash)
- **28**: Voice + Telegram + external extensions completamento

## 7. CONSTITUTION (12 regole — vedi AGENTS.md per dettaglio)

Root cause sempre (R1), integration test (R2), worktree isolati (R3), regole prima agenti (R4),
evidence verificabile (R5), planner prevede tutto (R6), esplorare prima (R7), no bypass (R8),
conserva contesto (R9), loop chiuso E2E (R10), workflow=contratto (R11), osservabilita' (R12).

## 8. WORKFLOW CONTRATTO (COMPLETO 12/12)

create -> validate -> Thor pre-review -> start -> spawn/worktree/monitor -> submit
-> reactor chain (task->wave->plan done) -> PlanCompleted -> Telegram -> post-review
-> auto-learning extraction -> worktree cleanup

## 9. LEARNINGS (28 totali — solo meta-pattern qui, dettaglio in git history)

**META-LEARNING**: Il sistema costruisce pezzi ma non li collega (pattern ricorrente).
Pianificazione bottom-up -> pezzi sconnessi. Fix: top-down, loop E2E prima, poi implementa.
Le 4 domande: chi produce input? chi consuma output? come l'utente lo vede? come il sistema registra?

Key learnings: worktree obbligatori (#4), integration test per wave (#13), AGENTS.md universale (#20),
solo merge commit (#23), waitpid non kill(0) (#21), sender diversi per IPC chain (#26).

## 10. ARCHITECTURE REVIEW (05 Aprile 2026)

> Base forte: plugin-based, daemon serio, spawn reale, mesh sync, observatory DB, inference HTTP.
> Gap rimanenti: extension contract parziale (no dispatcher), runtime provider-coupled.
> 4/6 gap originali FIXED in sessione 5 (monitor, eventi, gates, tasks_done).
> Rischi mitigati in Step 4: artifact, approval, compensation, scheduler, security, evaluation.
> Sessione 7: agent runtime completo (context API, live adaptation, auto-respawn).
> Sessione 8: self-build, harness engineering, MLX backend. Benchmark: Qwen 7B Coder MLX > Gemma 3 4B.

## 11. APPENDICI

### Daemon info
Porta: 8420 | Token: `Bearer dev-local` | Build: `cd daemon && cargo build --release`
Logs: `/tmp/convergio-daemon.{log,err}` | Service: launchd `com.convergio.daemon.plist`
CLI: `cvg status`, `cvg plan list`, `cvg agents list`, `cvg cheatsheet`

### Repo
convergio (daemon), convergio-frontend (cockpit), convergio-design (DS), ConvergioPlatform (archive)

### Guardrails
G1-G5: git hooks (MainGuard, FileSizeGuard 250, SecretScan, SqliteBlock, CommitLint)
C1-C10: Claude hooks in `.claude/settings.json`

### Fase 32g: Long-run autonomo (DONE — sessione 7)
Daemon gestisce checkpoint/resume/respawn. Auto-respawn con max 5 tentativi, budget propagation.
Contesto pieno -> checkpoint -> spawn continuation -> riprende. PR #97.

### Competitive positioning
Differenziatore: rete di organizzazioni autonome con marketplace.
Piu' forte di CrewAI/AutoGen (infrastruttura), LangGraph (piu' "OS"), OpenHands (governance).
Da rubare da mesh-llm: subprocess plugin, blackboard gossip, Nostr discovery.
