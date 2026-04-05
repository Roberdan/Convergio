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
| Test passanti (`cargo test --workspace`) | 990 (verificato sessione 8) |
| Righe Rust totali | ~53.400 |
| Endpoint HTTP unici | ~160 |
| Tabelle DB (via migrations) | 61+ |
| PR mergiate | 103 |

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
- **Inference**: HTTP calls reali Ollama/OpenAI-compatible + echo fallback
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
- **Frontend / Cockpit operativo**: backend forte ma ancora poco visibile; manca la superficie per vedere, capire e governare agenti/piani in tempo reale

Diagnosi sessione 8: Step 0-5 COMPLETI (Fase 26 self-build DONE, PR #103). 28 crate, 21 extension, 990 test, 103 PR. Sessione 8 in corso: Fase 49 (harness engineering).

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
| -- | Frontend / Cockpit operativo | -- | DA FARE — control plane realtime sopra DB/SSE/API esistenti, non dashboard passiva |

### Step 5: Self-hosting — DONE (sessione 8)

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 26 | Self-build extension | #103 | Build/test/deploy pipeline, CLI, 5 endpoint, 15 test |

## 5. FASI IN CORSO

Sessione 8 su M5 Max. Sessione M1 Pro prossima.

## 6. FASI FUTURE (ordinate per priorita')

### Fase 49: Harness Engineering — REVISIONE

**IMPORTANTE**: NON duplicare nel filesystem quello che sta gia' nel DB.
Il DB ha gia': plans/tasks (= feature_list), agent_activity (= progress),
plan_metadata (= learnings), task_evidence (= pass/fail). Il pattern Anthropic
(feature_list.json, progress.txt) e' per chi NON ha un daemon con DB. Noi ce l'abbiamo.

**Cosa tenere del pattern Anthropic**:
- [ ] Baseline test obbligatorio prima di ogni sessione (cargo test + curl health)
- [ ] Thor come evaluatore SEPARATO (modello/prompt diverso dal coding agent)
- [ ] UNA feature alla volta per sessione (enforced nel TASK.md)
- [ ] L'agente LEGGE dal DB via context API (32e), NON da file .md statici

**Cosa NON fare**:
- NON creare feature_list.json — usare i task nel piano
- NON creare progress.txt — usare agent_activity nel DB
- NON duplicare stato in file quando il DB e' la source of truth

### Frontend / Cockpit operativo — PRIORITA' ALTA

**Obiettivo**: rendere il daemon visibile e governabile in tempo reale.
Convergio ha gia' orchestrazione, monitor, event bus, observatory, Thor,
approval, evidence e agent runtime. Quello che manca e' la superficie operativa
unificata per l'umano.

**Perche'**: oggi il backend puo' anche fare la cosa giusta, ma se Roberto non
vede in un colpo d'occhio piani, agenti, blocchi, costi, evidence e review,
il sistema sembra morto o opaco. Il cockpit chiude il loop lato operatore.

**Scope minimo del primo rilascio**:
- [ ] Plan/Agent board realtime via SSE: plans, waves, tasks, agents, status, progress
- [ ] Observatory UI: timeline, search, dashboard, anomaly, metriche gia' presenti nel daemon
- [ ] Agent debugger: log tail, stato corrente, ultimi eventi, worktree/branch/PR/diff, interrupt/retry/priority change
- [ ] Gates visibili: Thor pre/post review, approval requests, blocker reason, evidence status
- [ ] Context panel: scope org/plan/task/repo/node, pins, artifact, learnings, convenzioni, token budget
- [ ] Cost surface: token/costo per agente, piano e sessione

**Regole di implementazione**:
- [ ] Source of truth = DB + SSE + API esistenti; NON duplicare stato in file frontend
- [ ] Prima control plane operativo, poi visual polish
- [ ] Prima superfici read/debug/control, poi editor/terminal avanzati
- [ ] Ogni widget deve rispondere alle 4 domande: input, consumatore, visibilita', stato registrato
- [ ] Ogni action dal cockpit deve lasciare evidence nel DB o in domain events

### Fase 50: Autoresearch loop — ottimizzazione continua notturna

**Obiettivo**: Applicare il pattern Karpathy (modifica->test->misura->keep/discard) a
tutti i progetti gestiti da convergio, non solo al daemon stesso.
**Motivazione**: Roberto: "non riusciamo ad applicarlo a tutti i progetti e alle org?"
Il loop gira di notte, locale, gratis. Ottimizza codice E costi token.

**Per il codice (ogni progetto)**:
- Agente locale (Qwen 27B su MLX) prova un'ottimizzazione su un crate
- cargo test + cargo bench = metrica oggettiva
- Migliore? keep + commit. Peggiore? revert.
- 100+ esperimenti a notte, zero costi API

**Per le organizzazioni (ottimizzazione token)**:
- Stesso task eseguito con Haiku vs Sonnet vs locale → misura qualita' + costo
- Se Haiku produce risultato accettabile → downgrade tier per quel tipo di task
- Il model router impara: "per task tipo X, Haiku basta" → 90% risparmio
- Dati in token_usage + agent_activity, gia' nel DB

**Task**:
- [ ] Loop controller nel daemon: scheduled task notturno (cron 02:00)
- [ ] Metrica oggettiva per tipo progetto: Rust=cargo test+bench, TS=vitest, Python=pytest
- [ ] Registra ogni esperimento in DB (tentativo, risultato, keep/discard)
- [ ] Usa modelli LOCALI (MLX), non API cloud — gratis
- [ ] Dashboard esperimenti: GET /api/autoresearch/results

### Fase 51: MLX diretto + TurboQuant — niente Ollama

**Obiettivo**: Inference locale via MLX diretto (non Ollama) con TurboQuant per context lunghi.
**Motivazione**: L'ADR 0302 di ConvergioPlatform gia' prevedeva "replace Ollama with lighter
embedded model". MLX e' nativo Apple Silicon, TurboQuant fa 4.6x compressione KV cache.
Su M1 Pro (32GB): Qwen 27B con context 128K invece di 16K.

**Architettura** (senza Ollama):
```
daemon → inference router → backend_mlx.rs → subprocess:
  python3 -m mlx_lm.generate --model qwen3.5-27b --turboquant --prompt "..."
```

Gia' usiamo questo pattern per TTS:
```
convergio-voice/tts_backends.rs → subprocess mlx_audio
```

**Vantaggi TurboQuant su M1 Pro (32GB)**:
- Senza: Qwen 27B Q4 = 16GB modello + 8GB KV = 24GB, context ~16K
- Con: 16GB modello + 1.7GB KV = 17.7GB, context **128K+**
- Oppure: modello 32-40B che prima non ci stava

**Task**:
- [ ] backend_mlx.rs in convergio-inference (subprocess mlx-lm, come tts_backends)
- [ ] Installare mlx-lm + turboquant su entrambi i nodi
- [ ] Config: CONVERGIO_MLX_MODEL=qwen3.5-27b, CONVERGIO_MLX_TURBOQUANT=true
- [ ] Test: inference locale con context 64K su M1 Pro
- [ ] Rimuovere dipendenza da Ollama dal daemon

### Fase 52: Kernel/Jarvis su M1 Pro — nodo voice/assistant

**Obiettivo**: M1 Pro e' il nodo per kernel, voice e Telegram. Non M5 Max.
**Motivazione**: Roberto: "voglio il kernel/jarvis sul m1pro"
M1 Pro con 32GB + TurboQuant MLX = Qwen 27B locale con context 128K.
Il kernel classifica messaggi Telegram, risponde se semplice, delega se complesso.

**Setup**:
- M1 Pro registrato nel mesh con capabilities: {voice: true, kernel: true, telegram: true}
- Daemon routing: task voice/kernel → M1 Pro
- Qwen 27B MLX come modello locale per classificazione e risposte
- TTS gia' funziona (mlx_audio). STT da completare (Whisper MLX).
- Telegram client gia' implementato (PR #44). Serve solo bot token in env.

**Task**:
- [ ] Registrare M1 Pro nel node capability registry con voice/kernel/telegram
- [ ] Configurare Telegram bot token su M1 Pro (~/.convergio/env)
- [ ] Watchdog locale: Qwen 27B classifica, risponde o escala (pattern ADR 0302)
- [ ] Telegram → kernel → risposta locale O delega a M5 Max/cloud
- [ ] Test: manda messaggio Telegram → kernel classifica → risponde

### Remaining
- **Frontend / Cockpit operativo**: rifare convergio-frontend come control plane realtime del daemon
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
> Prossimo salto di potenza: cockpit operativo che renda tutto questo visibile, debuggabile e governabile in tempo reale.

## 11. APPENDICI

### Daemon info
Porta: 8420 | Token: `Bearer dev-local` | Build: `cd daemon && cargo build --release`
Logs: `/tmp/convergio-daemon.{log,err}` | Service: launchd `com.convergio.daemon.plist`
CLI: `cvg status`, `cvg plan list`, `cvg agents list`, `cvg cheatsheet`

### Repo
convergio (daemon), convergio-frontend (cockpit operativo), convergio-design (DS), ConvergioPlatform (archive)

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
