# Convergio — Master Tracker

> Creato: 03 Aprile 2026 | Ultimo aggiornamento: 04 Aprile 2026 (sessione 5)
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

## 3. STATO ATTUALE (04 Aprile 2026 sessione 5 — onesto)

### Numeri

| Metrica | Valore |
|---------|--------|
| Crate nel workspace | 26 |
| Extension registrate in main.rs | 19 (tutte con `routes()` -> `Some`) |
| Test passanti (`cargo test --workspace`) | 850 |
| Righe Rust totali | ~51.000 |
| Endpoint HTTP unici | ~115 |
| Tabelle DB (via migrations) | 59+ |
| PR mergiate | 69 |

### Cosa funziona realmente (verificato con smoke test)

- **Daemon boot**: main.rs -> pool -> migrations -> 19 extension -> routes -> serve
- **Auth**: Bearer token + dev-mode localhost bypass
- **Config hot-reload**: watcher con debounce 500ms
- **WAL checkpoint**: graceful shutdown
- **Plan CRUD**: create/list/get/start/complete/cancel/checkpoint
- **Plan protocol**: objective/motivation/requester required, validate endpoint
- **Plan lifecycle**: task submitted -> wave done -> plan done (AUTOMATICO, sessione 5)
- **Thor plan review**: pre-review required before plan start, post-review on completion
- **IPC**: agents, messages, channels, context, SSE stream
- **Mesh batch sync**: export/import via HTTP con HMAC auth + background loop
- **Extension routes**: 19/19 registrate, tutte rispondono a curl
- **SSE domain events**: PlanCreated, TaskCompleted, WaveCompleted, PlanCompleted
- **Evidence gates**: record/query/gates/preflight (column names fixed sessione 5)
- **Billing metering**: usage/invoices/rates/alerts
- **Observatory**: timeline/search/dashboard/anomaly (persiste in DB)
- **Agent spawning**: reale con monitor, worktree, push, PR automatica
- **Inference**: HTTP calls reali Ollama/OpenAI-compatible + echo fallback
- **Depgraph**: wired in main.rs, 19 componenti, graph validation
- **Health/Metrics**: /api/health/deep (19 componenti), /api/metrics (33+ metriche)
- **launchd**: plist con PATH completo, daemon rebuild dopo PR merge

### Cosa NON funziona (remaining gaps)

| Componente | Stato | Gap |
|-----------|-------|-----|
| **File transport (rsync)** | ASSENTE | Nessun modo di copiare repo + .env a nodo remoto |
| **Delegation orchestrator** | ASSENTE | Nessun componente che lega copy -> spawn -> monitor -> sync back |
| **Node capability registry** | ASSENTE | Tutti i nodi identici, nessun routing per capability |
| **Worktree cleanup** | ASSENTE | Worktree e branch non puliti dopo plan done |
| **Learning automatico** | ASSENTE | PM compila manualmente, non automatico |

**Diagnosi sessione 5**: Il loop si chiude. Il daemon non e' piu' un API layer passivo —
spawna agenti, monitora, avanza wave/piani automaticamente, emette domain events per la UI.
Il gap critico e' la delegation multi-nodo (rsync + remote spawn).

### Workflow — stato buchi (aggiornato sessione 5)

| Step | Stato | Note |
|------|-------|------|
| 1. Problema->Piano | OK | objective/motivation/requester required |
| 2. Piano->Wave/Task | OK | validate endpoint, task create API |
| 3. Thor pre-review | OK | gate enforced su plan start |
| 4. Spawn->commit->push+PR | OK | -- |
| 5. Task->submitted | OK | monitor chiama API, IPC emesso |
| 6. Wave auto-progression | OK | reactor conta pending, avanza |
| 7. Plan->done | OK | automatico via reactor chain |
| 8. Domain events SSE | OK | TaskCompleted, WaveCompleted, PlanCompleted |
| 9. Telegram notifica | OK | fire-and-forget (serve bot token in env) |
| **10. Cleanup** | MANCA | Worktree/branch non puliti | future |
| **11. Learning auto** | MANCA | Manuale | future |

## 4. FASI COMPLETATE (storia collassata)

### Infrastruttura core (Wave A) — DONE

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 0 | Pulizia | SKIP | Nuovo repo, niente da pulire |
| 1 | convergio-types + Extension trait | -- | Config, errors, Extension trait. 2 test |
| 2 | convergio-telemetry | -- | logging, health, metrics. 6 test |
| 3 | convergio-db | -- | Pool r2d2, MigrationRunner, helpers. 10 test |
| 4 | convergio-security | -- | JWT, audit, RBAC. 8 test |
| 5 | convergio-ipc | -- | 11 moduli, SSE, agent registry. 29 test |
| 6 | convergio-mesh | -- | 14 moduli, HMAC auth, delta sync, delegation. 36 test |

### Orchestrator + CLI (Wave B) — DONE

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 7 | convergio-orchestrator | -- | Plans, tasks, waves, Thor, reaper. 40 test |
| 8 | convergio-cli | -- | 75 moduli, pure HTTP client. 209 test |

### Server + Extensions (Wave C) — DONE

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 9 | convergio-server | -- | 12 moduli, middleware, router. 34 test |
| 10 | Extensions (kernel, org, voice) | #5 | 57 test totali |

### Intelligence + Ecosystem (Wave D) — DONE

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 11 | Inference routing | #7 | Model router semantico, budget-aware. 15 test |
| 12 | Prompt management + skill registry | #6 | Template engine, A/B test, spawn injection. 23 test |
| 12b | Skill/agent prompts migration | #33 | 8 skills + workflow pipeline seeded |
| 13 | Org-as-Package | #8 | Installer, sandbox, signing, delegation. 46 test |
| 13b | Project scaffolding (`cvg project init`) | #37 | -- |
| 14 | HTTP Extension bridge | #9 | Health polling, webhook, proxy. 22 test |

### Runtime + Platform (Wave E) — DONE

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 15 | Long-running execution | #11 | Heartbeat, checkpoint, resume, delegation chain. 36 test |
| 16 | Depgraph validation + OpenAPI | #10 | Kahn's algo, SemVer check, OpenAPI gen. 30 test |
| 17 | Agent runtime | #13 | Allocator, scope, scheduler, concurrency. 39 test |
| 18 | MCP server | #12 | JSON-RPC 2.0, 15 tools, ring access control. 29 test |
| 18b | Billing & inter-org economics | #14 | Metering, budget hierarchy, invoices. 21 test |
| 18c | Backup & disaster recovery | #15 | Retention, snapshot, restore, export. 30 test |
| 18d | Multi-tenancy & org isolation | #16 | 5 livelli isolamento. 25 test |

### Observability + Governance (Wave F) — DONE

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 19 | Observatory | #18 | Timeline, FTS5 search, anomaly detection. 15 test |
| 20 | Evidence gate + workflow | #17 | 3 gates, preflight, Thor auto-enqueue. 31 test |

### Wiring + Integration (Phase 21-24) — DONE

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 21 | Wiring + smoke test | -- | 18 extension, 71+ migrations, 100+ endpoint |
| 22 | Migrazione dati | -- | PARTIAL — scripts pronti, cutover manuale pending |
| 23a | Wire existing routes | #25 | prompts, backup |
| 23b | Create routes.rs | #25,#26 | ipc, mesh, orchestrator, evidence, longrunning, voice |
| 23c | Replace stubs | #29 | org, org-package, kernel. Path param fix `:id` |
| 23d | End-to-end verification | #32 | PARTIAL — SSE done, depgraph done. Mesh 2-nodi deferred |
| 24a-d | Plan protocol | #30 | Schema, tracking, gates, aggregation. 825 test |
| 24e-f | PM endpoints + protocol | #35 | PM analyze/digest/learnings/forecast |

### Guardrails + Migration (Phase 27-29) — DONE

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 27a | Rules + git hooks | #27 | .claude/settings.json + 10 script hooks |
| 27b | Skills + commands | #33 | 8 skill prompts + workflow pipeline |
| 27c | Agent definitions | #36 | Agent TOML definitions |
| 27d | Config + reference | #34 | models.yaml, schemas, reference docs |
| 29a | CONSTITUTION + README | #31 | 9 regole + 16 learnings |

### Agent Spawning + Lifecycle (Phase 32) — DONE

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 32 | Agent spawning reale | #38,#40,#41,#42,#45 | spawn -> worktree -> monitor -> push -> PR |
| 30 | Mesh sync loop | #43 | Background sync attivo |
| 33 | Telegram client | #44 | Implementato, manca bot token in env |
| 38c | launchd + daemon ops | PARTIAL | plist + install script. Firewall non gestibile |

### Step 0: Loop chiuso (Phase 32b-d) — DONE (sessione 5)

| Fase | Titolo | PR | Note |
|------|--------|-----|------|
| 32b | Agent->Plan lifecycle wiring | #63,#65,#66,#67 | pending count fix, IPC sender fix, domain events, wave/plan auto-progression |
| 32c | Planner E2E enforcement | #68 | objective/motivation/requester required, POST /api/plan-db/validate |
| 32d | Thor plan-level review | #69 | POST /api/plan-db/review (pre), /validate-completion (post), gate su plan start |
| -- | Task create API | #64 | POST /api/plan-db/task/create |

**Smoke test verificato**: create -> review(pass) -> start -> evidence -> submit -> reactor chain -> plan done (automatico).

## 5. FASI IN CORSO

### Step 1: Fondamenta
- **23e**: DepgraphExtension gia' wired in main.rs (PR #48). Verificare.

## 6. FASI FUTURE (ordinate per priorita')

### Step 1: Fondamenta (NEXT)
- **23e**: DepgraphExtension gia' wired (PR #48). Verificare startup validation.

### Step 2: Delegation pipeline
- **31**: File transport (rsync wrapper tra nodi)
- **37b**: Node capability registry (GPU, voice, compute)
- **34**: Delegation orchestrator (copy -> spawn -> monitor -> sync back -> notify)
- **35**: E2E integration test (delegate hello-world a localhost)

### Step 3: Completamento
- **32e**: Agent context API (contesto live dal DB, non file statici)
- **32f**: Agent live adaptation (checkpoint polling, IPC alerts, file sentinel)
- **36b**: Inference reale (Ollama/API, non echo per tutti i tier)
- **36c**: STT Whisper (trascrizione locale reale)
- **39b**: Progetti non-codice (report, business docs, evidence non-code)
- **40b**: Integration test HTTP (830 unit + E2E)
- **Frontend**: rifare convergio-frontend dentro Convergio (agenti via daemon)

### Step 4: Production hardening (Wave I)
- **41**: Artifact model (output non-code: report, PDF, screenshot)
- **42**: Human-in-the-loop (approvazione umana con soglie)
- **43**: Compensation/rollback (wave failure -> compensazione automatica)
- **44**: Scheduler policy (capability, costo, privacy, locality)
- **45**: Security remote execution (trust levels, sandbox, mTLS)
- **46**: Evaluation framework (precision/recall planner e Thor)

### Step 5: Self-hosting
- **26**: Convergio costruisce convergio

### Fasi non completate (bassa priorita')
- **22**: Cutover (manuale, quando Roberto decide)
- **25**: Script->daemon (deprecare script bash)
- **27e**: Hooks Claude operativi (PreCompact, context exhaustion, etc.)
- **27f**: Script operativi triage
- **28**: Voice + Telegram + external extensions completamento
- **12c**: Agent catalog completo (68 agenti -> TOML specs)
- **13b**: Project scaffolding completamento

## 7. CONSTITUTION (regole 1-12)

1. **Mai la via breve** — sempre root cause. 3 fix consecutivi con nuovi problemi -> STOP.
2. **Integration test obbligatorio** — unit test verdi != "funziona". Smoke test E2E obbligatorio.
3. **Isolamento workspace** — worktree separato. Mai checkout principale. Un worktree = un branch = una PR.
4. **Regole prima degli agenti** — le regole esistono PRIMA di lanciare gli agenti.
5. **Evidence verificabile** — mai "done" senza proof. Thor valida.
6. **Il planner prevede tutto** — integration test per wave, wiring verification, smoke test finale.
7. **Prima esplorare, poi costruire** — MAI costruire senza verificare cosa esiste gia'.
8. **Mai bypassare senza approvazione** — nessun hook/gate/check skippato senza OK esplicito dell'utente.
9. **Conserva il contesto** — non rileggere file gia' letti. Offset/limit per file grandi. Delega task meccanici.
10. **Loop chiuso E2E** — input -> elaborazione -> output -> feedback -> stato aggiornato -> visibile all'utente.
11. **Workflow = contratto** — solve->planner->execute->thor enforced dal sistema. Ogni transizione validata, registrata, emessa, verificabile.
12. **Auto-organizzazione = osservabilita'** — ogni azione ha un costo, ogni risultato una qualita', ogni errore un learning.

## 8. WORKFLOW CONTRATTO (aggiornato sessione 5 — tutto OK tranne cleanup/learning)

```
1. PROBLEMA -> POST /api/plan-db/create (objective+motivation+requester REQUIRED)
2. PIANIFICAZIONE -> planner crea wave/task -> POST /api/plan-db/validate
3. REVIEW -> POST /api/plan-db/review -> Thor pre-review (GATE: must pass)
4. START -> POST /api/plan-db/start/:id (blocked senza review pass)
5. ESECUZIONE -> spawn -> worktree -> monitor -> commit -> push -> PR
   -> task submitted -> TaskCompleted event -> SSE
6. REACTOR CHAIN -> task_done -> wave_done -> auto-validate
   -> tasks promoted to done -> wave done -> plan_done
7. COMPLETAMENTO -> plan status=done -> PlanCompleted event -> Telegram
8. POST-REVIEW -> POST /api/plan-db/validate-completion (evidence, cost)
9. CLEANUP -> worktree/branch cleanup [MANCA]
10. LEARNING -> PM aggrega [MANCA: manuale]
```

## 9. LEARNINGS (cronologico, 1-24)

| # | Titolo | Root cause | Fix/Regola |
|---|--------|-----------|------------|
| 1 | 10056: 38 task submitted senza verifica | Workflow senza match commit->task | Evidence verificabile |
| 2 | 10056: 4 task fraudolenti | Evidence self-reported | Verifica indipendente |
| 3 | 10056: Thor mai invocato | Wave completion senza trigger | Thor automatico su wave |
| 4 | Agenti paralleli senza worktree | Nessun isolamento filesystem | Worktree obbligatori (R3) |
| 5 | Regole aggiunte a sessione in corso non lette | Agenti gia' partiti | Regole PRIMA degli agenti (R4) |
| 6 | Agenti non fanno checklist se non la conoscono | Checklist assente al lancio | Checklist nel tracker dall'inizio |
| 7 | `claude -p` con prompt >3000 chars = hang | Prompt troppo lungo come arg shell | Prompt corto + file istruzioni |
| 8 | `</dev/null` con `claude -p` = errore | stdin chiuso con -p | Non usare </dev/null con -p |
| 9 | Heredoc con backtick = unexpected EOF | Backtick in heredoc bash | Prompt in file separati |
| 10 | Pattern funzionante Claude non-interattivo | -- | `timeout N claude --dangerously-skip-permissions -p "Leggi <file>"` |
| 11 | Orchestratore non pulisce worktree post-merge | Prompt incompleto | Cleanup in checklist |
| 12 | Orchestratore autonomo funziona (6 fasi) | -- | Pattern prototipo per agent runtime |
| 13 | GRAVE: crate isolati senza integration testing | Ogni fase testa solo il suo crate | Integration test per wave (R2) |
| 14 | Orchestratore automatico produce crate vuoti | Ottimizza per "compila", non "funziona" | routes()->Some + curl obbligatorio |
| 15 | Bottom-up building senza composizione | Piano tratta crate come unita' indipendenti | Integration test cross-crate |
| 16 | Agenti delegati non fanno cargo fmt | Pre-commit hook assente | cargo fmt in checklist |
| 17 | Delegation accoppiata a singolo modello | Spawner solo per Claude | Multi-provider (inference router -> spawner) |
| 18 | Health/metrics wired ma non registrati | main.rs non completa il loop | Wiring completo in main.rs |
| 19 | Agenti non aggiornano i piani | Monitor non chiude il loop | Fase 32b: monitor->task->plan |
| 20 | CLAUDE.md accoppiato a un solo provider | Solo Claude legge CLAUDE.md | AGENTS.md universale |
| 21 | kill(pid,0) non rileva zombie | kill ritorna 0 per zombie | waitpid(WNOHANG) |
| 22 | nohup + cd chain = tutti stessa directory | cd nella stessa shell | Subshell isolata per agente |
| 23 | Squash merge perde lavoro agenti paralleli | Squash riscrive storia | Solo merge commit (enforced) |
| 24 | EventBus->SSE ma non->DB = eventi persi | Nessun sink persistente | Observatory sink->obs_timeline |

| 25 | Evidence gate column mismatch | Gate usa task_id/kind, tabella ha task_db_id/evidence_type | Fix nomi colonne (#65) |
| 26 | IPC self-message skip breaks chain | Reactor skips msg from ali-orchestrator, tutti gli emit usano ali-orchestrator | Sender diverso: task-updater, orchestrator-reactor (#66,#67) |
| 27 | SQL predicate "submitted" non escluso | on_task_done conta submitted come pending | Aggiungere submitted alla exclusion list (#63) |
| 28 | Tracing logs su stderr, non stdout | launchd scrive stdout/stderr separati, tracing va su stderr | Guardare /tmp/convergio-daemon.err |

**META-LEARNING**: Il sistema costruisce pezzi ma non li collega (pattern ricorrente).
Pianificazione bottom-up -> pezzi sconnessi. Fix: top-down, loop E2E prima, poi implementa.
Le 4 domande: chi produce input? chi consuma output? come l'utente lo vede? come il sistema registra?

## 10. ARCHITECTURE REVIEW (04 Aprile 2026 — feedback esterno)

### Giudizio
> Convergio ha una base forte e rara. Ma il centro di gravita' oggi e':
> daemon modulare + worktree runtime + DB/SSE observability
> non ancora: sistema che pianifica/esegue/valida/sincronizza/chiude il loop da solo.

### Cosa e' vero nel codice
1. Architettura plugin-based reale (Extension, Manifest, AppContext)
2. Boot daemon serio (registra, migra, monta, health, metrics, on_start)
3. Spawn agenti reale (worktree, TASK.md, processo, log, monitor, push, PR)
4. Mesh sync con background loop reale
5. Observatory persiste in DB (non solo SSE volatile)
6. Inference con backend HTTP reali (Ollama/OpenAI-compatible)

### Dove il codice NON chiude il loop (aggiornato sessione 5)
1. ~~Spawn monitor incompleto~~ FIXED (#63): monitor -> task submitted -> reactor chain
2. ~~Eventi sottoutilizzati~~ FIXED (#63): PlanCompleted, WaveCompleted, TaskCompleted emessi
3. ~~Gate non enforced~~ FIXED (#68,#69): StartGate + ThorPreReview enforced
4. ~~tasks_done mai aggiornato~~ FIXED (#63): incrementato in emit_task_lifecycle
5. Extension contract parziale (subscriptions/on_event/scheduled_tasks no dispatcher)
6. Runtime provider-coupled (solo ClaudeCli e Script)

### Confronto competitivo

| vs | Convergio piu' forte | Convergio piu' debole |
|---|---|---|
| CrewAI/AutoGen | Infrastruttura: DB, routes, health, Git/PR | Collaboration patterns |
| LangGraph | Piu' "OS" e meno libreria | State machine/debuggability |
| Temporal | Piu' vicino al mondo agenti/coding | Durable workflow, compensation |
| OpenHands | Governance, modularita', control plane | Loop esecutivo agentico puro |

### Rischi -> fasi aggiunte
Artifact model (41), Human approval (42), Compensation (43),
Scheduler policy (44), Security remote (45), Evaluation (46).

## 11. APPENDICI

### Daemon info
- Porta: 8420. Token: `Bearer dev-local`
- CLI: `cvg status`, `cvg plan list`, `cvg agents list`, `cvg cheatsheet`
- Build: `cd daemon && cargo build --release`
- Logs: `/tmp/convergio-daemon.log`, `/tmp/convergio-daemon.err`
- Service: launchd `com.convergio.daemon.plist`

### Repo coinvolti

| Repo | Path | Scopo |
|------|------|-------|
| convergio | `/Users/Roberdan/GitHub/convergio` | Daemon + backend |
| convergio-frontend | `/Users/Roberdan/GitHub/convergio-frontend` | Cockpit UI |
| ConvergioPlatform | `/Users/Roberdan/GitHub/ConvergioPlatform` | Vecchio monolite (archive) |
| convergio-design | `/Users/Roberdan/GitHub/convergio-design` | Design system |

### Frontend stato
Fasi 29-38 DONE. CI verde, 96 unit test, 58 E2E.
Bug aperti: mobile search, Manettino responsive, SteppedRotary, 13 lint warnings.
E2E Playwright e responsive deferred.

### Come delegare a Copilot
```bash
cd .worktrees/<task> && gh copilot --model claude-opus-4-6
```
Delegare: merge worktree, migrazione singoli crate (meccanico).
NON delegare: decisioni architetturali, risoluzione conflitti, validazione finale.

### Piano 10056 — Task assorbiti

| Task | Assorbito in |
|------|-------------|
| F-41 Remove CRSQLite | Fase 0 |
| F-42 Remove __disabled | Fase 0 |
| F-49 Circuit breaker mesh | Fase 6 |
| F-50 HMAC replay | Fase 6 |
| F-51 In-memory IPC | Fase 5 |
| F-20/21 Rate limiter/conn limit | Fase 5 |
| F-44/47 Delta/parallel sync | Fase 6 |
| F-60 Prometheus metrics | Fase 2 |
| F-34/35/37/38 Stub removal | Fase 0 |

### DB ownership

| Modulo | Tabelle |
|--------|---------|
| db (core) | _schema_registry, _sync_meta, _sync_conflicts |
| orchestrator | plans, tasks, waves, plan_reviews, deliverables, projects, workspaces, token_usage, agent_activity, plan_metadata, delegation_log |
| ipc | ipc_agents, ipc_messages, ipc_subscriptions, ipc_budget_log, ipc_model_registry, ipc_node_capabilities, ipc_file_locks, ipc_org_members, ipc_agent_skills |
| mesh | mesh_sync_stats, mesh_peer_state, peer_heartbeats, host_heartbeats, coordinator_events, delegation_progress |
| security | audit_log, ipc_auth_tokens |
| kernel | kernel_config, kernel_events, knowledge_base, domain_skill_map |
| org | notification_queue, notifications, decision_log |

### Guardrails (Fase 27a)

| # | Guard | File |
|---|-------|------|
| G1 | MainGuard | `scripts/hooks/git-pre-commit.sh` |
| G2 | FileSizeGuard (250 lines) | `scripts/hooks/git-pre-commit.sh` |
| G3 | SecretScan | `scripts/hooks/git-pre-commit.sh` |
| G4 | SqliteBlock | `scripts/hooks/git-pre-commit.sh` |
| G5 | CommitLint | `scripts/hooks/git-commit-msg.sh` |
| C1-C10 | Claude hooks | `.claude/settings.json` |

### Competitive analysis detail
- **vs mesh-llm**: orthogonal (GPU pooling vs agent orchestration). Da rubare: subprocess plugin, blackboard gossip, Nostr discovery.
- **vs claw-code/oh-my-codex/openclaw**: nessuno ha Extension system, semantic manifest, org-as-package.
- Differenziatore: rete di organizzazioni autonome con marketplace.
