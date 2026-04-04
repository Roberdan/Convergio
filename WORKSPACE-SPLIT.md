# Convergio Workspace Split — Tracker

> Creato: 03 Aprile 2026
> Obiettivo: Da monolite (129K righe) a sistema modulare espandibile.
> Metodo: Niente piano DB, niente workflow. Lavoro diretto, review manuale, un crate per PR.
> Principio: il sistema deve permettere a organizzazioni autonome di pluggare moduli
> (kernel, org, voice, openclaw, ...) senza toccare il core.

## LEGGIMI PRIMA — Istruzioni operative per Claude

**Questo documento è la specifica completa.** Tu (Claude, sessione nuova) devi:

1. Leggere TUTTO questo file prima di fare qualsiasi cosa
2. Verificare lo stato corrente (quali fasi sono completate, checkbox)
3. Riprendere dalla fase assegnata (o la prima non completata)
4. Aggiornare le checkbox e le Note man mano che lavori
5. Quando il contesto si riempie, aggiornare questo file e dire all'utente di aprire una nuova sessione

### Struttura obbligatoria di ogni fase (TEMPLATE)

Ogni fase è un progetto auditabile. Deve avere TUTTI questi campi. Se un campo manca, la fase non è pronta per essere eseguita. Se il report finale manca, la fase non è chiusa.

```
### Fase N: Titolo descrittivo

**Obiettivo**: Cosa deve fare questa fase in 1-2 frasi. Specifico, verificabile.
**Motivazione**: Perché serve. Quale problema risolve. Quale valore porta.
**Committente**: Chi l'ha ordinata (Roberto, piano automatico, learning da incidente, etc.)
**Deps**: Fasi che devono essere completate prima.

#### Task
- [ ] Task 1 — descrizione concreta con criterio di accettazione
- [ ] Task 2 — ...

#### Report finale (compilato a chiusura)
- **Stato**: DONE / PARTIAL (specificare cosa manca) / BLOCKED (specificare blocco)
- **PR**: #numero
- **Date**: inizio — fine
- **Cosa è stato fatto**: lista concreta dei deliverable
- **Cosa NON è stato fatto**: lista onesta di cosa manca e perché
- **Test evidence**: N test verdi, smoke test result, curl output rilevante
- **Key Learnings**: cosa abbiamo imparato che influenza le fasi future
  (errori fatti, decisioni architetturali, scoperte, regole da aggiungere)
- **Impatto su fasi successive**: cosa cambia per il piano a valle
```

**Regole per chi scrive il report:**
- Essere onesti. "PARTIAL" è meglio di "DONE" con cose nascoste che mancano.
- I key learnings NON sono opzionali. Ogni fase insegna qualcosa.
- "Cosa NON è stato fatto" è il campo più importante del report.
  È la coda di lavoro che la prossima fase eredita.
- Il report si scrive A CHIUSURA della fase, non prima.
  Non inventare risultati — documenta quelli reali.

### Checklist di chiusura fase (OBBLIGATORIA)

Ogni fase DEVE chiudersi con TUTTI questi step. Non procedere alla fase successiva senza averli completati.

1. **cargo check --workspace** — tutto il workspace deve compilare, non solo il tuo crate
2. **cargo test -p <tuo-crate>** — tutti i test del crate devono passare
3. **cargo test --workspace** — verifica di non aver rotto nulla negli altri crate
4. **Aggiorna il tracker** — segna le checkbox completate, scrivi le Note con: moduli creati, numero test, decisioni prese
5. **Commit** — nel tuo worktree, messaggio conventional commit, con Co-Authored-By
6. **PR** — `gh pr create` verso main, con summary e test plan
7. **PR review** — dopo la creazione, controlla i commenti di review (CI, Copilot, umani):
   - Leggi TUTTI i commenti con `gh pr view <N> --comments` e `gh api repos/Roberdan/convergio/pulls/<N>/comments`
   - Per ogni commento che ha senso: fixa, committa, pusha sul branch
   - Per commenti che NON hanno senso: rispondi spiegando perché non li applichi
   - **NON mergiare finché ci sono commenti aperti non risolti**
   - Dopo i fix: ri-verifica cargo check + cargo test --workspace
8. **Verifica** — `git status` pulito, niente file dimenticati
9. **Cleanup post-merge** — dopo che la PR è mergiata:
   - `git worktree remove .worktrees/fase-N --force`
   - `git branch -D feat/fase-N-crate-name`
   - `git remote prune origin`
   - Verifica: `git worktree list` e `git branch` non devono avere residui

Se un test fallisce: fixalo prima di committare. Se rompi un altro crate: fixalo o chiedi all'utente.
Non lasciare MAI una fase con test rossi o workspace che non compila.
Non lasciare MAI una PR con commenti di review non risolti.

### Isolamento agenti paralleli (OBBLIGATORIO)

**Problema**: agenti paralleli che lavorano nello stesso checkout si pestano i piedi (branch spuri, commit nel posto sbagliato, conflitti).

**Soluzione**: ogni fase gira in un **worktree separato**, poi fa **PR su main**.

```bash
# 1. Crea worktree DENTRO il progetto (MAI in /tmp o altrove)
cd /Users/Roberdan/GitHub/convergio
git worktree add .worktrees/fase-<N> main

# 2. Lavora SOLO nel tuo worktree
cd .worktrees/fase-<N>

# 3. Crea branch, committa, pusha
git checkout -b feat/fase-<N>-<nome-crate>
# ... lavora ...
git add <solo i tuoi file>
git commit -m "feat: ..."
git push -u origin feat/fase-<N>-<nome-crate>

# 4. Crea PR
gh pr create --base main --title "feat: fase N — <crate>" --body "..."

# 5. Pulisci worktree dopo merge
cd /Users/Roberdan/GitHub/convergio
git worktree remove .worktrees/fase-<N>
```

**I worktree stanno SEMPRE in `.worktrees/` dentro il repo.** Mai in /tmp, mai in /private, mai fuori dal progetto. Così li vedi, li controlli, e non spariscono.

**Regole ferree**:
- **MAI lavorare direttamente in `/Users/Roberdan/GitHub/convergio`** — solo worktree
- **MAI committare su main** — solo PR da branch
- **MAI toccare file di altri crate** — se devi modificare un crate non tuo, chiedi all'utente
- **Un worktree = una fase = un branch = una PR**
- Se hai bisogno di codice di un'altra fase in corso, aspetta che venga mergiata

### Repo coinvolti

| Repo | Path locale | Scopo |
|------|------------|-------|
| ConvergioPlatform | `/Users/Roberdan/GitHub/ConvergioPlatform` | Vecchio monolite. Sorgente da cui migrare. |
| convergio | `/Users/Roberdan/GitHub/convergio` | Nuovo repo. Destinazione. |
| convergio-frontend | `/Users/Roberdan/GitHub/convergio-frontend` | Frontend (NON toccare) |
| convergio-design | `/Users/Roberdan/GitHub/convergio-design` | Design system (NON toccare) |

### Regole operative (da ConvergioPlatform CLAUDE.md)

- **MAI commit su main direttamente** — hook `MainGuard` blocca. Usa worktree detached HEAD.
- **MAI creare branch** — hook blocca. Usa `git worktree add --detach <path> HEAD`.
- **MAI usare `sqlite3` direttamente** — hook blocca. Usa `cvg` CLI o API HTTP `:8420`.
- **MAI pipe a tail/head/grep/cat** — hook blocca. Usa Read/Grep/Glob.
- **Max 250 righe per file** — hook `FileSizeGuard` blocca.
- **Lingua**: codice/docs in English, conversazione in italiano.
- **Nel NUOVO repo `convergio`**: usa worktree + PR (vedi sezione "Isolamento agenti paralleli"). MAI committare su main direttamente.

### Come mergiare un worktree su ConvergioPlatform

```bash
# 1. Vai nel worktree
cd /private/tmp/cvg-w1-security

# 2. Verifica che compila
cd daemon && cargo check --features kernel

# 3. Torna a main
cd /Users/Roberdan/GitHub/ConvergioPlatform

# 4. Cherry-pick i commit (NON merge, NON rebase)
git cherry-pick <commit-hash>

# 5. Se conflitto: risolvi, git add, git cherry-pick --continue

# 6. Dopo merge: pulisci worktree
git worktree remove /private/tmp/cvg-w1-security
```

### Come delegare a Copilot (Opus 4.6)

Per task meccanici e ben definiti (un crate alla volta):

```bash
# Opzione 1: script convergio
cd /Users/Roberdan/GitHub/ConvergioPlatform
scripts/platform/copilot-worker.sh <task_description> --model claude-opus-4.6

# Opzione 2: diretto
gh copilot --model claude-opus-4.6
# Poi dare il prompt con contesto dal tracker
```

**Cosa delegare**: merge worktree, migrazione singoli crate (meccanico)
**Cosa NON delegare**: decisioni architetturali, risoluzione conflitti, validazione finale

### Come continuare quando finisce il contesto

Quando senti che il contesto si sta riempendo (80+ turni, risposte che degradano):

1. **Aggiorna questo file**: segna le checkbox completate, aggiungi note
2. **Scrivi lo stato esatto**: cosa hai fatto, cosa resta, dove ti sei fermato
3. **Di' all'utente**: "Contesto pieno. Aggiornato il tracker. Apri una nuova sessione e dammi `cat ~/Desktop/WORKSPACE-SPLIT.md`"
4. La nuova sessione legge il file e riprende esattamente da dove ti sei fermato

### Cosa deve fare l'utente a mano

- Approvare tool call (edit, bash, write)
- Confermare merge/push
- Decidere sui conflitti cherry-pick
- Avviare nuove sessioni quando il contesto si riempie
- Opzionalmente: verificare cargo check/test dopo ogni fase

### Ordine di esecuzione

```
Sessione A: Merge worktree ConvergioPlatform (vedi sezione "Pre-condizioni") — SKIP (no worktree pending)
Sessione B: Setup nuovo repo convergio (CLAUDE.md, Constitution, Cargo.toml stub) — DONE 2026-04-03
Sessione C: Fase 0 — Pulizia (cancellare TUI, stubs, cruft) — SKIP (new repo, nothing to clean)
Sessione D: Fase 1 — convergio-types (già scaffolded, completare) — DONE 2026-04-03
Sessione E: Fase 2 — convergio-telemetry
...continua dal tracker, una fase per sessione
```

Ogni sessione inizia con: `Leggi ~/Desktop/WORKSPACE-SPLIT.md e riprendi da dove siamo rimasti`

---

## Visione architetturale

Convergio è una **rete di organizzazioni AI autonome che fanno business**.
Il daemon è l'infrastruttura invisibile sotto — come internet per le aziende.
Il valore è nelle organizzazioni e negli agenti, non nel daemon.

### Tre layer

```
EXTENSION (pluggabili, sostituibili)     ← il business vive qui
  kernel/Jarvis, org chart, voice, openclaw, evolution, ...

SERVIZI PIATTAFORMA (orchestrano)        ← il coordinamento vive qui
  orchestrator, agent catalog, inference routing

INFRASTRUTTURA (il daemon core)          ← deve essere perfetto e invisibile
  types, telemetry, db, security, ipc, mesh, server, cli
```

### Core loop (MUST work perfectly)
```
Goal → Org routing → Agent assignment → Model selection → Execution → Evidence → Thor → Sync
```

### Principio fondamentale
Il daemon non sa cosa fanno gli agenti. Non sa che Elena fa legal review.
Sa solo: c'è un task, serve un agente con capability X, assegnalo, traccia, valida.

### Identità, comunicazione, osservabilità (NON-NEGOTIABLE)

**1. Tutto ha un nome.** Ogni agente, ogni org, ogni extension, ogni nodo mesh.
Non "agent-7f3a", ma "Elena" su "Legal Corp" su "M5Max".
Il nome è persistente, visibile, e usato in ogni log, evento, messaggio.

**2. Tutti parlano con tutti.** Agenti nella stessa org, tra org diverse, tra nodi.
Elena su M5Max chiede a Baccio su M1Pro una review. Il bus lo gestisce trasparentemente.
L'utente vede: "Elena → Baccio: review contratto sezione 4" — non "agent-a → agent-b: msg".

**3. Tutto è visibile in tempo reale.** Ogni azione, ogni messaggio, ogni cambio di stato
è un evento streamabile via SSE. La UI mostra il sistema vivo:
- Chi sta lavorando su cosa, adesso
- Messaggi tra agenti in tempo reale
- Flusso di task tra org
- Costi che si accumulano
- Health di ogni nodo/modulo
- Grafo delle delegazioni attive

Il feed è filtrabile: "mostrami solo Legal Corp" o "solo mesh traffic" o "solo errori".

### Principi

1. **Extension architecture** — kernel, org, voice, openclaw sono plugin, non core
2. **Interfaccia unica (NON-NEGOTIABLE)** — un solo modo per registrarsi, comunicare, loggare, telemetria. Chi non implementa Extension non esiste. Zero alternative, zero workaround.
3. **Semantic self-description** — ogni modulo dichiara cosa offre (provides), cosa richiede (requires), che tool espone. Il sistema si auto-regola: routing, degradazione, onboarding.
4. **Ogni modulo possiede le sue tabelle** — le registra via trait, il core le migra
5. **Resilienza è una proprietà, non un servizio** — ogni modulo gestisce i suoi retry/circuit breaker
6. **Telemetria unica** — tutti si registrano allo stesso collector
7. **CLI = client HTTP puro** — zero import internals
8. **Server = routing shell** — la logica vive nei crate, server fa solo wiring
9. **Long-running first** — il sistema gestisce nativamente esecuzioni di ore/giorni con heartbeat, checkpoint, resume, budget tracking
10. **Future-proof** — aggiungere un modulo = creare un crate + impl Extension trait + zero modifiche al core
11. **Agent runtime = compiler runtime** — il daemon gestisce gli agenti come un compilatore gestisce la memoria: allocation (spawn), ownership (org), borrowing (delegation), lifetime (heartbeat), GC (reaper). La concorrenza tra agenti segue gli stessi principi: scheduling fair, deadlock prevention, backpressure, sync/async orchestration.

## Extension Contract (IL CONTRATTO)

Un solo trait. Un solo modo di esistere nel sistema.
Due modalità: Rust nativo (compilato) o HTTP bridge (qualsiasi linguaggio).

### Rust Extension (interna)

```rust
pub trait Extension: Send + Sync {
    fn manifest(&self) -> Manifest;

    // DB
    fn migrations(&self) -> Vec<Migration> { vec![] }

    // Routes
    fn routes(&self, ctx: &AppContext) -> Option<Router> { None }

    // Lifecycle
    fn on_start(&self, ctx: &AppContext) -> Result<()> { Ok(()) }
    fn on_shutdown(&self) -> Result<()> { Ok(()) }

    // Telemetria (unico sistema)
    fn health(&self) -> Health { Health::Ok }
    fn metrics(&self) -> Vec<Metric> { vec![] }

    // Domain events (unico bus)
    fn subscriptions(&self) -> Vec<EventFilter> { vec![] }
    fn on_event(&self, event: &DomainEvent) {}

    // Schedulazione
    fn scheduled_tasks(&self) -> Vec<ScheduledTask> { vec![] }

    // Hot-reload config
    fn on_config_change(&self, key: &str, value: &Value) -> Result<()> { Ok(()) }
}
```

### HTTP Extension (esterna — qualsiasi linguaggio)

```
POST /api/extensions/register
{
    "id": "openclaw-bridge",
    "manifest": { "provides": [...], "requires": [...] },
    "base_url": "http://localhost:3100",
    "health_endpoint": "/health",
    "events_webhook": "/webhook/events",
    "routes_prefix": "/api/ext/openclaw"
}
```

Il daemon tratta entrambe identicamente: stesse validazioni, stesso health check,
stessa telemetria, stesso event bus. Bridge pattern: prova via HTTP, internalizza se serve.

### Manifest semantico

```rust
pub struct Manifest {
    pub id: &'static str,            // "convergio-mesh"
    pub description: &'static str,   // per LLM e umani
    pub version: Version,
    pub kind: ModuleKind,            // Core | Extension | Integration

    pub provides: Vec<Capability>,   // cosa offro (con SemVer)
    pub requires: Vec<Dependency>,   // cosa mi serve (con version_req)
    pub agent_tools: Vec<ToolSpec>,  // tool invocabili dagli agenti
}

pub struct Capability {
    pub name: &'static str,
    pub version: &'static str,       // "2.1.0"
    pub description: &'static str,
    pub sla: Option<Sla>,
}

pub struct Dependency {
    pub capability: &'static str,
    pub version_req: &'static str,   // ">=2.0, <3.0"
    pub required: bool,              // false = degrada gracefully
}
```

Il sistema usa i manifest per:
- `cvg capabilities` → lista automatica di tutto
- Routing: "chi sa fare peer-sync?" → mesh
- Degradazione: mesh down → chi dipende da peer-sync degrada
- Onboarding: openclaw dichiara requires:["db-pool","ipc-bus"] → il sistema verifica
- LLM reasoning: Jarvis legge i manifest e sa a chi delegare
- SemVer check: orchestrator vuole peer-sync >=2.0 ma mesh offre 1.5 → errore all'avvio

### Domain Events (NUOVO)

Ogni evento ha: chi (nome, non ID), cosa, quando, dove (nodo), contesto (org/plan).

```rust
pub struct DomainEvent {
    pub actor: ActorName,       // "Elena" / "Legal Corp" / "convergio-mesh"
    pub action: EventKind,
    pub timestamp: DateTime,
    pub node: String,           // "M5Max"
    pub context: EventContext,  // org_id, plan_id, task_id se applicabile
}

enum EventKind {
    // Orchestrazione
    PlanCreated { plan_id: i64, name: String },
    TaskAssigned { task_id: i64, agent: String, org: String },
    TaskCompleted { task_id: i64, evidence: Evidence },
    // Comunicazione (visibile in real-time)
    MessageSent { from: String, to: String, preview: String },
    DelegationStarted { from_org: String, to_org: String, task: String },
    // Sistema
    AgentOnline { name: String, org: String, node: String },
    AgentOffline { name: String, reason: String },
    HealthDegraded { module: String, reason: String },
    SyncConflict { table: String, local: Value, remote: Value },
    BudgetAlert { org: String, spent: f64, limit: f64 },
    ExtensionLoaded { id: String, version: Version },
}
```

Ogni evento è:
- Streamabile via SSE (`GET /api/events/stream?filter=org:Legal+Corp`)
- Persistito per replay/audit
- Sottoscrivibile da extension (Rust: on_event(), HTTP: webhook)
- Visualizzabile nella UI in tempo reale con nomi umani, non ID

### API exposure layers

Ogni Extension dichiara le sue route, ma non tutto è uguale:

| Layer | Chi accede | Operazioni | Esempio |
|-------|-----------|------------|---------|
| **Public** | UI, CLI, agenti | CRUD completo | plans, tasks, agents, orgs, delegations |
| **System** | Moduli interni, admin dashboard | Read + ops limitate | _schema_registry, heartbeats, checkpoints, reaper status |
| **Private** | Solo il modulo owner | Mai esposto via HTTP | crypto keys, HMAC secrets, nonce internals |

Regole:
- Ogni entità Public ha CRUD completo con validazione
- La UI costruisce su Public API — deve poter gestire TUTTO il business
- System API è read-only per la UI (dashboard ops) ma writable internamente
- Private = zero route HTTP, zero accesso esterno, il modulo lo gestisce da solo
- Ogni operazione CRUD valida le dipendenze incrociate prima di eseguire

### Dependency validation (NON-NEGOTIABLE)

```rust
fn validate_dependency_graph(extensions: &[Box<dyn Extension>]) -> Result<()>
```

Eseguita:
- All'avvio del daemon (fail-fast se grafo rotto)
- Prima di disabilitare/rimuovere un modulo (blocca se rompe dipendenze)
- Nella UI (mostra grafo, evidenzia cosa si romperebbe)
- Detect circular dependencies

### Long-running execution protocol

Per moduli come openclaw che girano ore/giorni:

```rust
pub trait LongRunnable: Extension {
    fn heartbeat_interval(&self) -> Duration;
    fn checkpoint(&self) -> Result<Checkpoint>;
    fn resume(&self, checkpoint: Checkpoint, ctx: &AppContext) -> Result<()>;
    fn progress(&self) -> Progress;  // pct, stage, cost, ETA
}
```

Il daemon gestisce: heartbeat monitor → reaper se stale → resume da checkpoint → budget guard → progress via SSE.

### Delegation chain

```rust
pub struct Delegation {
    pub id: String,
    pub parent_id: Option<String>,   // chi mi ha delegato
    pub agent_id: String,
    pub budget: Budget,              // ereditato dal parent, mai superiore
    pub deadline: Option<DateTime>,
}
```

Albero completo: se B muore → A notificato. Budget A esaurito → tutti i figli fermati.
Progresso aggregato su tutta la catena.

---

## DB Architecture (NUOVO)

### Problema oggi
43 tabelle create in modo sparso, senza ownership. Migrazioni monolitiche in migrations.rs.
Nessun concetto di "questo modulo possiede queste tabelle".

### Modello target
Ogni crate definisce le sue migrazioni via trait:

```rust
pub trait DbExtension {
    fn name(&self) -> &str;
    fn version(&self) -> u32;
    fn migrations(&self) -> Vec<Migration>;
}
```

Il core `convergio-db` fornisce:
- Pool r2d2 condiviso
- Migration runner che raccoglie tutte le extension e le esegue in ordine
- Tabella `_schema_registry(module TEXT PK, version INT, applied_at TEXT)`
- Helpers: table_exists, column_exists, transaction wrappers

### Ownership tabelle

| Modulo | Tabelle |
|--------|---------|
| **db (core)** | _schema_registry, _sync_meta, _sync_conflicts |
| **orchestrator** | plans, tasks, waves, plan_reviews, deliverables, projects, workspaces |
| **ipc** | ipc_agents, ipc_messages, ipc_subscriptions, ipc_budget_log, ipc_model_registry, ipc_node_capabilities, ipc_file_locks, ipc_org_members, ipc_agent_skills |
| **mesh** | mesh_sync_stats, mesh_peer_state, peer_heartbeats, host_heartbeats, coordinator_events, delegation_progress |
| **security** | audit_log, ipc_auth_tokens |
| **orchestrator** | execution_runs, workspace_events, session_state |
| **kernel** | kernel_config, kernel_events, knowledge_base, domain_skill_map |
| **org** (extension) | notification_queue, notifications, decision_log |

### Regola: ogni crate porta le sue migrazioni, il runner le applica all'avvio

---

---

## Decisione strategica: nuovo repo o refactor?

**Decisione: NUOVO REPO** — migrazione chirurgica, non riscrittura.

1. Creare nuovo repo `convergio.io` (o `convergio`)
2. Struttura workspace da zero con il layout di questo documento
3. Migrare crate per crate dal vecchio repo — muovere e adattare, NON riscrivere
4. Il vecchio repo `ConvergioPlatform` diventa read-only archive
5. Ogni crate migrato porta i suoi test

Motivazioni:
- Repo attuale ha 845 commit di storia, 784MB .git, 70GB target/
- Cruft ovunque: CommandCenter, demo, dist, coverage, PARITY.md, NEXT_SESSION.md
- Struttura a workspace dal giorno zero, non rincorsa
- Segnale forte: prodotto, non prototipo

## UI: tutto pronto per convergio-frontend (NON-NEGOTIABLE)

Ogni API, ogni evento, ogni entità DEVE essere pensata per la UI:
- **CRUD completo** su ogni entità Public → la UI ci costruisce sopra
- **SSE event stream** con nomi umani → la UI mostra il sistema vivo in real-time
- **OpenAPI auto-generato** da ogni Extension → la UI sa cosa chiamare
- **Filtri su tutto** → la UI filtra per org, agente, nodo, tipo evento
- **WebSocket per brain/dashboard** → stato aggiornato senza polling
- **Grafo dipendenze serializzabile** → la UI lo visualizza

Regola: se un dato o un'azione non è raggiungibile via API, non esiste.
La CLI e la UI devono poter fare le stesse identiche cose.

## Cose da cancellare

### Dentro daemon/src/
- [ ] TUI intera (src/tui/, 70 file, 10.2K righe)
- [ ] Channel stubs email/slack (src/channels/email.rs, slack.rs + test)
- [ ] __disabled_pending_api_migration feature flag
- [ ] crsqlite refs residui + tabelle crsql_*

### Fuori daemon/ (cruft repo)
- [ ] CommandCenter/ (SwiftUI archiviato, 7 file)
- [ ] dashboard_web/ (dir vuota)
- [ ] demo/ (2 HTML statici)
- [ ] dist/ (vuoto)
- [ ] coverage/ (vuoto)
- [ ] plans/ (8 YAML vecchi, piani vivono nel DB)
- [ ] types/dummy.ts (file morto)
- [ ] convergio-architecture.html (snapshot statico)
- [ ] daemon.log (log file nel repo)
- [ ] NEXT_SESSION.md (obsoleto, v19.2.0)
- [ ] PARITY.md (audit vecchio)
- [ ] config/llm/litellm.yaml + docs/adr/ADR-0127-litellm-internalization.md

## Workspace target

```
daemon/
  Cargo.toml                   # [workspace]
  crates/
    ── INFRASTRUTTURA (perfetta e invisibile) ──
    convergio-types/            # contratti, Extension trait, Manifest, DomainEvent
    convergio-telemetry/        # tracing, metrics, health aggregator
    convergio-db/               # pool, migration runner, _schema_registry
    convergio-security/         # auth, HMAC, crypto, audit_log
    convergio-ipc/              # message bus, SSE, domain events
    convergio-mesh/             # peer discovery, sync, delegation
    convergio-server/           # Axum routing shell, extension wiring
    convergio-cli/              # cvg (HTTP client puro)

    ── SERVIZI PIATTAFORMA (orchestrano il business) ──
    convergio-orchestrator/     # plans, tasks, waves, Thor, reaper
    convergio-agents/           # catalogo agenti, org routing, model preferences

    ── EXTENSION (pluggabili, opzionali) ──
    convergio-kernel/           # Jarvis (Qwen locale + Telegram + voice)
    convergio-org/              # org chart, inter-org comms, provisioner
    convergio-voice/            # STT/TTS engine (usato da kernel)

  src/main.rs                   # binary: collects extensions, starts daemon
  src/mcp_server/main.rs        # MCP binary
```

Extension esterne (non Rust, si registrano via HTTP):
- evolution (TypeScript) → POST /api/extensions/register
- openclaw (Node.js) → POST /api/extensions/register
- convergio-community skills → POST /api/extensions/register

## Org-as-Package (ECOSYSTEM)

Chiunque può pubblicare un'organizzazione pronta all'uso.
Zero compilazione. Pacchetto dichiarativo: TOML + SQL + prompts + Docker opzionale.

### Installazione
```bash
cvg org install crm-corp                                    # da registry
cvg org install https://github.com/sara-dev/crm-corp        # da GitHub
cvg org install ./my-org/                                    # locale
```

### Formato pacchetto
```
org-name/
  manifest.toml        # identità, capabilities, permissions, requirements
  agents/*.toml        # agent specs (nome, ruolo, model, tools, prompt ref)
  prompts/*.md         # prompt templates
  migrations/*.sql     # tabelle prefissate (crm_*, legal_*, ...)
  service/             # opzionale: Docker/processo per logica custom
```

### Sicurezza (3 livelli)

| Livello | Meccanismo |
|---------|-----------|
| **Trust pacchetto** | Firma autore verificata all'install. UNSIGNED = warning. Registry curated. |
| **Sandbox runtime** | DB: solo tabelle con prefisso. Route: solo sotto prefix. IPC: solo canali dichiarati. Budget: hardcap. Dati altrui: zero. |
| **Token scoped** | Ogni org ha un token con permessi, budget, expiry. Middleware enforza ad ogni chiamata. |

### Inter-org communication
Org A delega a Org B via bus. Daemon verifica: can_delegate, can_receive, budget.
L'utente vede in real-time: "Sara (CRM Corp) → Elena (Legal Corp): review contratto"

## Grafo dipendenze

```
types (zero deps) ← Extension trait vive qui
  |
  ├── telemetry -> types
  ├── db -> types
  ├── security -> types
  |
  ├── ipc -> types, db, telemetry
  ├── mesh -> types, db, security, telemetry
  ├── orchestrator -> types, db, ipc, telemetry
  |
  ├── server -> types, db, telemetry + raccoglie Extension da tutti
  ├── cli -> types (HTTP only, zero deps interne)
  |
  └── extensions (ognuna -> types, db, telemetry)
      ├── kernel -> types, db, ipc, telemetry
      ├── org -> types, db, telemetry
      └── voice -> types, kernel, telemetry
```

## Fasi di lavoro

### Fase 0: Pulizia
- [ ] Cancellare TUI (src/tui/, pub mod tui in lib.rs, match in main_dispatch.rs, ratatui+crossterm deps)
- [ ] Cancellare channel stubs email/slack
- [ ] Cancellare codice morto (litellm, dummy.ts, dist/, coverage/)
- [ ] Rimuovere feature flag __disabled_pending_api_migration
- [ ] Rimuovere refs crsqlite orfani
- [ ] cargo check + cargo test dopo pulizia
- Note: ___

### Fase 1: convergio-types + Extension trait
- [x] Creare crates/convergio-types/
- [x] Muovere: errors.rs, message_error.rs, config/, platform_paths.rs
- [x] Definire Extension trait (migrations, routes, health, metrics)
- [x] Definire Migration struct, HealthStatus, Metric
- [x] Primitive resilienza: RetryPolicy, CircuitBreaker
- [x] cargo check + cargo test
- Note: Config types migrati come struct pure (no I/O). Config loading/validation/watcher vanno in server (Fase 9). message_error semplificato (rimossi ssh2, rusqlite — da aggiungere quando servono). 2 test passano (platform_paths).

### Fase 2: convergio-telemetry
- [x] Creare crates/convergio-telemetry/
- [x] Tracing subscriber setup (da daemon_logging.rs)
- [x] MetricsCollector: raccoglie metriche da tutte le extension
- [x] HealthAggregator: /health/deep compone tutti i moduli
- [x] cargo check + cargo test
- Note: 3 moduli: logging.rs (tracing+panic hook), health.rs (HealthRegistry+HealthCheck trait, 4 test), metrics.rs (MetricsCollector+MetricSource trait, 2 test). Server-specific telemetry (request counters, middleware) rimane per Fase 9.

### Fase 3: convergio-db
- [x] Creare crates/convergio-db/
- [x] Pool r2d2, busy_timeout=5000
- [x] MigrationRunner: raccoglie DbExtension, applica in ordine, traccia in _schema_registry
- [x] Query helpers, transaction wrappers
- [x] Muovere solo tabelle core: _sync_meta, _sync_conflicts, _schema_registry
- [x] cargo check + cargo test
- Note: 4 moduli: pool.rs (r2d2 + PRAGMAs, 1 test), migration.rs (MigrationRunner + _schema_registry, 3 test), helpers.rs (table_exists/column_exists/is_busy_error, 5 test), core_tables.rs (_sync_meta + _sync_conflicts, 1 test). background_sync → mesh (Fase 6). CRDT/crsqlite rimosso (legacy).

### Fase 4: convergio-security
- [x] Creare crates/convergio-security/
- [x] impl Extension: porta audit_log, ipc_auth_tokens
- [x] Auth middleware, HMAC verify, crypto helpers
- [x] cargo check + cargo test
- Note: 4 moduli: types.rs (SecurityError, AclRule, AuditEntry, AgentBudget), jwt.rs (HMAC-SHA256 JWT issue/validate, AgentRole, 2 test), audit.rs (hash-chain audit trail, 2 test), rbac.rs (route-level RBAC per role, 4 test). Auth HTTP middleware → server (Fase 9). HMAC mesh → mesh (Fase 6).

### Fase 5: convergio-ipc
- [x] Creare crates/convergio-ipc/
- [x] impl Extension: porta ipc_agents, ipc_messages, ipc_subscriptions, etc.
- [x] Message bus, SSE, agent registry
- [x] cargo check + cargo test
- Note: 11 moduli: schema.rs (3 migration versions: core tables, model/budget, org+triggers), types.rs (AgentInfo, MessageInfo, ChannelInfo, BudgetEntry/Status/Alert, FileLock, ModelEntry, etc.), agents.rs (register/unregister/list/heartbeat/prune, 4 test), messaging.rs (send/broadcast/receive/receive_wait/history con rate limiting e atomic claim, 4 test), channels.rs (channel CRUD + shared context LWW + cleanup/vacuum, 3 test), skills.rs (skill registry con confidence scoring weighted average, 4 test), budget.rs (usage logging, daily summary, cost estimation, threshold alerts, 4 test), locks.rs (exclusive file locks con PID-aware cleanup, 3 test), models.rs (model registry, node capabilities, subscriptions, ollama/lmstudio probing, 3 test), sse.rs (EventBus broadcast + async SSE stream con heartbeat e lag detection, 1 test), ext.rs (Extension trait impl con manifest, health, metrics). 29 test passano. Org tables e isolation triggers inclusi. Apple FM bridge escluso (specifico di kernel).

### Fase 6: convergio-mesh
- [x] Creare crates/convergio-mesh/
- [x] impl Extension: porta mesh_sync_stats, peer_heartbeats, etc.
- [x] Peer discovery, sync, delegation
- [x] background_sync migra qui (dipende da db)
- [x] cargo check + cargo test
- Assorbe 10056: F-44 delta sync, F-49 circuit breaker, F-50 HMAC replay
- [x] Schema version guard: il mesh deve rifiutare sync da peer con schema version diversa. Controllare _schema_registry di entrambi i nodi prima di apply_changes. Se mismatch → log warning, skip sync, notifica che il peer deve aggiornarsi.
- Note: 14 moduli: error.rs (MeshError, 3 test), schema.rs (2 migration versions: core mesh tables + coordinator/delegation, 3 test), types.rs (SyncMeta, SyncChange, MeshStats, DelegateStatus/Result, SYNC_TABLES, 2 test), peers_types.rs (PeerConfig, PeersRegistry, PeersError), peers_parser.rs (INI parse/serialize, 2 test), peers_registry.rs (load/save/mutate/coordinator/active, 4 test), auth.rs (HMAC-SHA256 challenge-response + load_shared_secret, 6 test), transport.rs (HTTP sync: send/fetch changes, resolve_best_addr multi-transport, HMAC headers, update_mesh_sync_stats), sync.rs (resolve interval, schema version guard via /api/health, sync_meta CRUD, sync_table_with_peer, 4 test), sync_apply.rs (export_changes_since + apply_changes with FK disable, 4 test), convergence.rs (SHA-256 checksum from plan/task/wave counts, drift detection >5min, 5 test), delegation.rs (record_step + get_progress, 3 test), ext.rs (MeshExtension impl Extension + HealthCheck + MetricSource: peers_online, total_synced, latency). 36 test passano. DelegateEngine SSH escluso (specifico di ConvergioPlatform, troppo accoppiato). Daemon sync TCP (crsqlite) rimosso (legacy).

---

## Execution waves (parallelismo)

Ogni wave contiene fasi che possono girare in parallelo (dipendenze già soddisfatte).
Lanciarle con sessioni Claude separate o copilot-worker.sh.

```
WAVE A ✅  Fasi 1-6    Infrastruttura core           DONE
WAVE B ✅  Fasi 7+8    Orchestrator ∥ CLI            DONE
WAVE C ✅  Fasi 9+10   Server wiring ∥ Extensions    DONE
WAVE D ✅  Fasi 11-14  Intelligence + ecosystem       DONE
WAVE E ✅  Fasi 15-18  Runtime + platform             DONE
WAVE F ✅  Fasi 19-20  Observability + governance     DONE
WAVE G     Fasi 30-35  Delegation pipeline (E2E)      ← NEXT — il gap critico
```

---

### WAVE B — Orchestrator + CLI (parallelo, tutte le deps sono DONE)

### Fase 7: convergio-orchestrator
- [x] Creare crates/convergio-orchestrator/
- [x] impl Extension: porta plans, tasks, waves, deliverables, projects, etc.
- [x] Plans, tasks, waves, Thor gate, reaper, workspace
- [x] cargo check + cargo test
- Deps: types✅, db✅, ipc✅, telemetry✅
- Note: 14 moduli migrati. types.rs, schema.rs (3 migrations), plan_hierarchy.rs, reactor.rs, handlers.rs, actions.rs, executor.rs, validator.rs, reaper.rs, policy.rs, rollback.rs, approval.rs, ext.rs (OrchestratorExtension impl Extension). 40 test passati. Delegation pipeline semplificata (via HTTP API daemon, no rsync/tmux diretto).

### Fase 8: convergio-cli
- [x] Creare crates/convergio-cli/
- [x] Muovere: cli_*.rs, cli/
- [x] Deve essere client HTTP puro — verifica zero use crate:: verso daemon internals
- [x] cargo check + cargo test
- Deps: types✅ (HTTP only)
- Note: 75 moduli migrati. Pure HTTP client: zero import convergio_core. Comandi server-side (Serve, Db, Hook, Daemon, Ipc, Tui) esclusi — restano nel daemon binary. 5 file adattati (setup, project, audit_project, reap, create_org) per rimuovere dipendenze daemon interne e sostituire con paths.rs locali o HTTP API. 209 test passati, 0 falliti.

### WAVE C — Server + Extensions (dopo wave B)

### Fase 9: convergio-server (routing shell)
- [x] Ristrutturare server come shell che raccoglie Extension.routes()
- [x] Logica business migra nei crate appropriati
- [x] Server diventa: middleware + routing + extension wiring
- [x] Config loading, validation, hot-reload watcher (dalla vecchia config/)
- [x] Auth middleware HTTP (dalla vecchia server/middleware.rs)
- [x] Request telemetry middleware (dalla vecchia server/telemetry.rs)
- [x] cargo check + cargo test
- Deps: types✅, db✅, telemetry✅, security✅
- Note: 12 moduli: lib.rs, config.rs (load/save TOML, 2 test), config_defaults.rs (template), config_validation.rs (8 test), config_watcher.rs (hot-reload debounce+diff, 4 test), state.rs (ServerState+ApiError, 1 test), middleware_auth.rs (JWT+Bearer+dev-mode+localhost+CORS+RBAC, 2 test), middleware_audit.rs (audit_log insert, 6 test), middleware_telemetry.rs (endpoint stats+histogram+request ID, 3 test), rate_limiter.rs (sliding window per-client, 3 test), router.rs (build_router wiring, 1 test), runner.rs (graceful shutdown+bind addr, 4 test). 34 test passano. AppContext in convergio-types aggiornato da placeholder a typed resource map (insert/get/get_arc). Router usa tower Extension layer per iniettare ServerState, permettendo merge di extension Router<()> con system routes. Mesh HMAC auth NON nel server — gestito dal mesh extension sulle sue route. Dipendenze: types, db, telemetry, security (no mesh/ipc/orchestrator). 374 test workspace passano, 0 falliti.

### Fase 10: Extensions (kernel, org, voice) — parallelo tra loro
- [x] convergio-kernel: impl Extension, feature-gated
- [x] convergio-org: impl Extension, porta notification_queue, decision_log
- [x] convergio-voice: impl Extension, behind feature flag
- [x] Ogni extension compila e testa indipendentemente
- [x] cargo check + cargo test per ognuna
- Deps: types✅, db✅, telemetry✅, ipc✅ (per kernel)
- Note: PR #5. 31 file, 2813 righe aggiunte. **voice** (8 moduli, 22 test): standalone STT/TTS, rimossa dipendenza da kernel — voice è ora foundation crate. TTS multi-backend (Voxtral MLX→Qwen3→macOS Say), Whisper ASR, wake word, intent extraction, audio util. **org** (6 moduli, 13 test): factory (mission/repo), provisioner HTTP, orgchart ASCII, repo scanner. 4 migration: notifications, notification_queue, notification_deliveries, decision_log. **kernel** (5 moduli, 22 test): Jarvis engine (local/cloud inference routing, classificazione deterministica), health monitor, evidence gate (Article VI), recovery chain, 4 migration: kernel_events, kernel_verifications, kernel_config, knowledge_base. 57 test totali, 0 falliti. Workspace 13 crate compila.

### WAVE D — Intelligence + Ecosystem (parallelo, dopo wave C)

### Fase 11: Inference routing + token optimization
- [x] Crate convergio-inference o dentro convergio-agents
- [x] Model router intelligente: sceglie modello in base a task complexity, budget, capability richiesta
- [x] Budget-aware routing: "task semplice → Haiku, task complesso → Opus, budget quasi finito → local"
- [x] Token tracking per agent/org/plan con costi aggregati in tempo reale
- [x] Sostituzione della fallback chain statica (t1/t2/t3/t4) con routing semantico
- [x] API: GET /api/inference/costs, GET /api/inference/routing-decision
- Deps: types✅, db✅, ipc✅ (budget), telemetry✅
- Note: PR #7. 10 file sorgente, 15 test. types.rs (tiers, request/response, cost records), router.rs (model router semantico: local-first, cost-aware, budget-aware), classifier.rs (classificazione tier basata su keyword, sostituisce catena statica t1-t4), budget.rs (token tracking SQLite per agent/org/plan con downgrade automatico), metrics.rs (statistiche rolling-window per modello: p50, p95, error rate), routes.rs (API endpoints), schema.rs (2 migrazioni: inference_costs, inference_budgets), ext.rs (Extension trait + HealthCheck + MetricSource). Codice migrato e adattato da ConvergioPlatform.

### Fase 12: Prompt management + skill registry
- [x] Prompt templates versionati con variabili (agent role, context, constraints)
- [x] Skill registry: agenti dichiarano skill, il sistema fa discovery e composizione
- [x] Prompt optimization: misura token usage per prompt, suggerisce compressione
- [x] A/B testing prompts: stesso task, prompt diversi, confronto risultati
- [x] **Prompt injection at spawn**: quando il daemon spawna un agente, il prompt include le regole operative correnti (isolation, checklist, scope). Non dopo, non "quando le legge" — al momento dello spawn. (Learning #5: regole aggiunte dopo il lancio non vengono mai lette)
- [x] **Prompt immutability during execution**: le regole nel prompt dell'agente sono immutabili per tutta la durata del task. Cambi alle regole si applicano solo ai nuovi spawn.
- [x] API: CRUD /api/prompts, /api/skills, /api/skills/search?capability=X
- Deps: types✅, db✅, ipc✅ (skill discovery)
- Note: PR #6. 12 file sorgente, 23 test. store.rs (CRUD prompt con auto-versioning), render.rs (template engine {{variable}} con stima token), skills.rs (registry, discovery per capability, confidence weighted moving average), optimizer.rs (tracking token usage, suggerimenti compressione), ab_test.rs (ciclo completo A/B test), spawn.rs (prompt injection at spawn con snapshot immutabile), routes.rs (API HTTP), ext.rs (Extension trait + HealthCheck + MetricSource). 3 migrazioni DB.

### Fase 13: Org-as-Package ecosystem
- [x] Implementare il formato pacchetto org (manifest.toml, agents/*.toml, prompts/*.md, migrations/*.sql)
- [x] `cvg org install` da registry, GitHub, o locale
- [x] Sandbox runtime: DB prefix, route prefix, IPC channel isolation, budget hardcap
- [x] Token scoped per org con permessi, budget, expiry
- [x] Firma pacchetto + verifica all'install
- [x] Inter-org delegation con verifica can_delegate/can_receive/budget
- Deps: types✅, db✅, security✅, ipc✅, org✅
- Note: PR #8. Crate convergio-org-package. 12 file, 46 test. manifest.rs (TOML parsing/validation), installer.rs (install da local/GitHub/registry, firma), sandbox.rs (DB/route/IPC prefix isolation, budget hardcap), token.rs (scoped org tokens con permessi, delegation, budget, expiry), signing.rs (HMAC-SHA256), delegation.rs (inter-org con trust lists, budget checks). 3 migrazioni DB.

### Fase 12b: Migrazione skill/agent prompts da ConvergioPlatform — DONE (PR #33)
- [x] Migrare 8 skill prompts → seeded in prompt_templates al boot del daemon
- [x] 69 agent definitions → già nel seed catalog (convergio-agents, 4 seed files)
- [x] Workflow solve→planner→execute→thor → pipeline dichiarativa in prompt_pipelines
- [ ] Formato org-as-package TOML per agent defs (nice-to-have, deferred)
- Note: Skills seeded idempotent al boot. 69 agenti nel catalog con 9 categorie.

### Fase 12c: Agent catalog — ogni agente funziona nel nuovo sistema
Ogni agent definition deve diventare un record completo che il daemon sa come spawnare.

- [ ] **Agent spec format**: nome, ruolo, org, model preference, budget, capabilities, prompt ref, escalation policy
- [ ] Mappatura 68 agenti esistenti alle 9 categorie:
  - core_utility (19): ali-orchestrator, thor, wanda, sentinel, taskmaster, socrates, diana, marcus, xavier, po, plan-reviewer, plan-business-advisor, plan-post-mortem, compliance-validator, context-optimizer, deep-repo-auditor, design-validator, doc-validator, strategic-planner
  - technical_development (10): baccio, rex, task-executor, task-executor-tdd, dario-debugger, marco-devops, omri-data-scientist, otto-performance, paolo-best-practices, adversarial-debugger
  - business_operations (10): andrea, sofia, marcello, davide, enrico, fabio, luke, anna, dave, steve
  - leadership_strategy (7): ali-CoS, amy-CFO, antonio, dan, domik, matteo, satya
  - compliance_legal (5): elena, luca, guardian, dr-enzo, sophia
  - specialized_experts (7): fiona, sam, wiz, behice, coach, giulia, jenny
  - design_ux (4): jony, sara, nasra, stefano
  - release_management (5): app-release-manager (x2), ecosystem-sync, feature-release-manager, mirrorbuddy
  - research_report (1): research-report-generator
- [ ] Ogni agente ha: model tier (t1-t4), max_tokens, hourly budget, escalation target
- [ ] `cvg agents list` mostra tutti con stato (available/busy/offline)
- [ ] `cvg agents spawn <name> --task <id>` spawna con workspace isolato
- [ ] Inter-agent delegation: baccio chiede a rex una review, il bus lo gestisce
- Deps: Fase 12 (prompt registry), Fase 17 (agent runtime), Fase 11 (inference routing)
- Note: Non basta migrare i file .md — il sistema deve sapere chi sono, cosa fanno, quanto costano, e come farli collaborare.

### Fase 13b: Project scaffolding (`cvg project init`)
- [ ] `cvg project init <name>` — wizard interattivo: nome, descrizione, linguaggio, licenza, visibilità
- [ ] Crea repo GitHub con gh API (o locale) con struttura pronta
- [ ] **CI auto-generato** per linguaggio: Rust→cargo check+test+clippy, TS→eslint+vitest, Python→ruff+pytest
- [ ] **Branch protection** configurata via GitHub API: require PR, require CI pass, no direct push
- [ ] **CODEOWNERS** generato dall'org owner
- [ ] **.gitignore** per linguaggio, CLAUDE.md template, LICENSE
- [ ] **Copilot/agent review** abilitato automaticamente sulle PR
- [ ] Template espandibili: l'org può dichiarare i suoi template di progetto nel manifest
- Deps: cli, security (token GitHub), org
- Note: Quello che oggi facciamo a mano (CI, branch protection, CODEOWNERS) deve essere automatico. Ogni progetto nasce già con i guardrail — non scritti, enforced.

### Fase 14: HTTP Extension bridge
- [x] POST /api/extensions/register per extension esterne (qualsiasi linguaggio)
- [x] Health check polling per HTTP extensions
- [x] Event webhook delivery (domain events → POST to extension webhook)
- [x] Route mounting sotto prefix dichiarato
- [x] Lifecycle: register → health check → active → degraded → removed
- Deps: types✅, server✅, telemetry✅
- Note: PR #9. Crate convergio-http-bridge. 8 moduli, 22 test. types.rs (BridgeState lifecycle), schema.rs (2 migrazioni), store.rs (CRUD), handlers.rs (Axum POST/GET/DELETE), health.rs (background polling 30s, active/degraded/removed transitions), webhook.rs (DomainEvent delivery + audit log), proxy.rs (route forwarding /api/ext/:id/*), ext.rs (Extension trait).

### WAVE E — Runtime + Platform (parallelo, dopo wave C)

### Fase 15: Long-running execution protocol
- [x] LongRunnable trait: heartbeat_interval, checkpoint, resume, progress
- [x] Heartbeat monitor → reaper se stale
- [x] Checkpoint persistence + resume da ultimo checkpoint
- [x] Budget guard: ferma esecuzione se budget esaurito
- [x] Progress via SSE: percentuale, stage, costo corrente, ETA
- [x] Delegation chain: albero completo, propagazione budget/deadline/morte
- Deps: types✅, db✅, ipc✅ (SSE), orchestrator✅
- Note: PR #11. Crate convergio-longrunning. 10 moduli, 36 test. traits.rs (LongRunnable trait), heartbeat.rs (register/beat/stale detection), reaper.rs (background stale finder + cascade death), checkpoint.rs (JSON save/load/clear), budget.rs (cost recording + limit enforcement + parent propagation), progress.rs (update/load + IPC EventBus publishing), delegation.rs (parent-child tree + recursive CTE cascade), schema.rs (3 migrazioni: lr_executions, lr_checkpoints, lr_heartbeats), ext.rs (Extension trait, 4 capabilities), types.rs (ExecutionStage, ProgressSnapshot, DelegationNode).

### Fase 16: Dependency graph validation + OpenAPI
- [x] validate_dependency_graph() all'avvio (fail-fast se grafo rotto)
- [x] Blocca rimozione modulo se rompe dipendenze altrui
- [x] SemVer check: capability version vs version_req
- [x] Circular dependency detection
- [x] Grafo serializzabile JSON per UI
- [x] OpenAPI auto-generato da Extension::routes() per ogni modulo
- [x] `cvg capabilities` lista automatica di tutto il sistema
- Deps: types✅ (Manifest, Capability, Dependency), server✅
- Note: PR #10. Crate convergio-depgraph. 8 moduli, 30 test. graph.rs (Kahn's algorithm circular detection, validate_dependency_graph), semver_check.rs (capability version vs version_req), removal.rs (block removal if breaks dependents), openapi.rs (OpenAPI 3.0 auto-gen from manifests), routes.rs (/api/capabilities), ext.rs (Extension trait + health + metrics).

### Fase 17: Agent runtime (memory model + concurrency)
- [x] **Allocation**: spawn agent con budget, capability, org, model preference
- [x] **Workspace isolation**: ogni agente riceve un workspace isolato
- [x] **Ownership**: ogni agente appartiene a un'org
- [x] **Scope enforcement**: un agente può toccare SOLO i file/tabelle del suo task
- [x] **Borrowing/Delegation**: agente prestato a un altro task/org con timeout
- [x] **Lifetime tracking**: heartbeat = proof of life
- [x] **GC/Reaper**: raccoglie agenti morti, task orfani, delegation scadute
- [x] **Scheduling**: priority queue per org/plan/urgency, fair scheduling
- [x] **Concurrency control**: wave ordering enforced
- [x] **Deadlock prevention**: detect circular delegation
- [x] **Backpressure**: coda bounded per org
- [x] **Autoscaling**: backlog/idle threshold checks
- [x] API: GET /api/agents/runtime
- Deps: types✅, db✅, ipc✅, orchestrator✅, inference✅
- Note: PR #13. Crate convergio-agent-runtime. 15 file, 39 test. allocator.rs (spawn/activate/stop), scope.rs (grant/revoke/check/enforce), heartbeat.rs (register/beat/stale), delegation.rs (borrow/return/circular detection), scheduler.rs (priority queue + backpressure), concurrency.rs (wave ordering + budget cycle + autoscale), reaper.rs (stale agents + expired delegations + orphan cleanup), routes.rs (live runtime view), ext.rs (Extension + health + metrics + scheduled_tasks). 5 tabelle DB.

### Fase 18: MCP server
- [x] Binary separato: convergio-mcp crate
- [x] Espone le capability del daemon come MCP tools (15 tools)
- [x] Bridge tra Claude Code/Copilot e le API del daemon
- Deps: types✅, server✅ (HTTP client to daemon API)
- Note: PR #12. Crate convergio-mcp. 10 file, 29 test. JSON-RPC 2.0 over stdio, ring-based access control (Core/Trusted/Community/Sandboxed), reqwest HTTP bridge, 15 tools (plans, tasks, agents, inference, capabilities). Migrato e semplificato dal vecchio monolite (43→15 tools).

### Fase 18b: Billing, metering & inter-org economics
Il sistema gestisce organizzazioni autonome che fanno business tra loro. Serve un layer economico.

- [x] **Metering**: ogni azione ha un costo tracciato — API call, token inference, compute time, storage
- [x] **Budget hierarchy**: platform budget → org budget → agent budget
- [x] **Inter-org billing**: costo addebitato a chi delega
- [x] **Rate cards**: ogni org dichiara prezzi per capability
- [x] **Invoice generation**: riepilogo periodico per org
- [x] **Cost alerts**: soglie configurabili con auto-pause
- [x] **Settlement**: log-only (chi deve cosa a chi)
- [x] **Audit trail economico**: hash chain SHA-256 tamper-evident
- [x] **Free tier / quotas**: quota giornaliera/mensile per org
- [x] API: GET /api/billing/usage, invoices, rates + POST alerts
- Deps: db✅, security✅, ipc✅, orchestrator✅, agent runtime✅
- Note: PR #14. Crate convergio-billing. 12 file, 21 test. metering.rs, budget.rs (hierarchy), rates.rs (rate cards + inter-org), invoices.rs, alerts.rs (70/85/95% + auto-pause), settlement.rs (debiti/crediti log), audit.rs (SHA-256 hash chain + verify_chain), routes.rs (4 endpoint).

### Fase 18c: Data retention, backup & disaster recovery
- [x] **Retention policy**: per tabella, configurabile per org
- [x] **Auto-purge**: scheduled task + log + SSE event
- [x] **DB backup**: snapshot atomico SQLite WAL + SHA-256 checksum
- [x] **Disaster recovery**: restore da snapshot con verifica
- [x] **Export/import org data**: JSON bundle self-describing
- Deps: db✅, scheduler✅, security✅
- Note: PR #15. Crate convergio-backup. 10 file, 30 test. retention.rs (per-table rules + auto-purge), snapshot.rs (atomic WAL checkpoint + checksum), restore.rs (pool/file restore), export.rs + import.rs (org data bundle), routes.rs (10 endpoint), ext.rs (2 scheduled tasks: purge 3AM, snapshot 4AM). 3 tabelle DB.

### Fase 18d: Multi-tenancy & org isolation hardening
- [x] **DB isolation**: ogni org ha un prefisso tabelle, validate_table_access() blocca cross-org
- [x] **Network isolation**: whitelist peer per org, open/strict mode
- [x] **Secret isolation**: namespace segreti per org, SHA-256 scope-based
- [x] **Audit isolation**: trail per-org con hash chain, query_org() + query_all() per admin
- [x] **Resource limits**: tracking soft CPU/mem/storage/agents/API calls, violation logging
- Deps: db✅, security✅, mesh✅, org✅
- Note: PR #16. Crate convergio-multitenancy. 10 file, 25 test. 5 livelli isolamento: DB, network, secret, audit, resource. Routes sotto /api/tenancy/*. Extension trait con health + metrics.

### WAVE F — Observability + Governance (dopo wave D+E)

### Fase 19: Observability aggregation layer
- [x] Timeline API: cronologia eventi cross-org con filtri composti
- [x] Search: ricerca full-text FTS5 su eventi, messaggi, audit
- [x] Dashboard aggregates: costo/ora, throughput task/giorno, latenza modello
- [x] Anomaly detection: spike costi, drop throughput, agenti idle
- [x] Export: Prometheus exposition format, webhook CRUD
- [x] API: GET /api/observatory/*
- Deps: tutto✅
- Note: PR #18. Crate convergio-observatory. 11 file, 15 test. timeline.rs (record + query filtri dinamici), search.rs (FTS5), dashboard.rs (aggregati + cache), anomaly.rs (cost spikes + idle agents), export.rs (Prometheus + webhooks), routes.rs + routes_webhook.rs (10 handler), ext.rs (scheduled anomaly_scan 15min). 5 tabelle DB (obs_timeline, obs_search FTS5, obs_anomalies, obs_dashboard_cache, obs_webhooks).

### Fase 20: Evidence gate + workflow automation
- [x] Evidence verificabile per ogni task (commit hash, test output, artifact)
- [x] **Checklist enforcement**: TestGate, ChecklistGate, ValidatorGate
- [x] **Pre-flight validation at spawn**: task exists, pending, wave deps completed
- [x] Thor automatico su wave completion
- [x] Commit-to-task matching (task-N/#N conventions)
- [x] Reaper per task stale con notifica dedup
- [x] Workflow blindato: lezioni operative diventano codice
- Deps: orchestrator✅, security✅, agent runtime✅
- Note: PR #17. Crate convergio-evidence. 10 file, 31 test. evidence.rs (record + query verifiable evidence), gates.rs (3 enforcement gates), preflight.rs (4 spawn precondition checks), workflow.rs (Thor auto-enqueue, stale detection, commit matching, background monitor 5min), ext.rs (Extension + health + metrics + scheduled tasks). 3 tabelle DB.

---

### Fase 21: Wiring + smoke test — il daemon che gira — DONE
- [x] **main.rs**: 18 extension registrate, pool condiviso, EventBus via AppContext
- [x] **Extension registry**: Vec<Arc<dyn Extension>>, on_start chiamato, routes montate
- [x] **Migration all'avvio**: 71+ migrations applicate automaticamente
- [x] **Smoke test**: daemon su :8420, /api/health → 200, 100+ endpoint funzionanti
- [x] **Integration test**: curl smoke test per ogni crate (fase 23a-23c)
- [x] **CLI connesso**: cvg status, cvg plan list, cvg agents list funzionano
- Note: Completata progressivamente attraverso fasi 23a-23d. SSE domain events wired (PR #32).

### Fase 22: Migrazione dati + cutover — PARTIAL
- [x] Script export-old-data.sh e import-new-data.sh esistono in scripts/
- [x] verify-parity.sh per verifica parità
- [x] cutover.sh per bootstrap
- [ ] Esecuzione cutover effettiva (richiede coordinamento manuale con vecchio daemon)
- [ ] Verifica parità dati post-cutover
- Deps: Fase 21 ✅
- Note: Scripts pronti. Cutover è un'operazione manuale one-time quando Roberto decide di switchare.

### Fase 23: Route wiring + stub replacement — crate per crate (AUDIT 2026-04-04)

**STATO**: 23a ✅, 23b ✅ (PR #25 + #26), 23c ✅ (PR #29), 23d parziale.
**PROSSIMO PASSO**: Fase 23d — full route audit, SSE domain events, mesh sync 2-nodi. Poi Fase 24.

Audit: 9/19 extension funzionano. 7 hanno codice ma routes()→None. 3 sono stub vuoti.
Ogni sub-task si chiude con: `cargo check && curl` al daemon. Learning #13 + #14.

#### 23a: Wire existing routes — DONE 2026-04-04 (PR #25)
- [x] **convergio-prompts**: ext.rs ora chiama `routes()` → 8 endpoint `/api/prompts/*`, `/api/skills/*`. Smoke 200.
- [x] **convergio-backup**: ext.rs ora chiama `router()` con BackupState → 10 endpoint `/api/backup/*`. Smoke 200.

#### 23b: Create routes.rs — DONE 2026-04-04 (PR #25)
- [x] **convergio-ipc**: routes.rs creato, 7 endpoint (status, agents, channels, context, messages, stream SSE, send).
- [x] **convergio-mesh**: routes.rs creato, 6 endpoint (status, peers, sync export/import/status, heartbeat). Schema fix peer_name vs peer.
- [x] **convergio-orchestrator**: plan_routes.rs + plan_routes_ext.rs creato, 14 endpoint plan-db CRUD (list, create, get, start/complete/cancel, task/update, wave/create/update, checkpoint save/restore, execution-tree, evidence).
- [x] **convergio-evidence**: routes.rs creato (PR #26), 7 endpoint (record, list, has, commits, gates, preflight, commit-match). Smoke 200.
- [x] **convergio-longrunning**: routes.rs creato (PR #26), 9 endpoint (heartbeat register/beat/stale, checkpoint CRUD, progress, delegation tree, budget). Smoke 200.
- [x] **convergio-voice**: routes.rs creato (PR #26), 3 endpoint (status, speak, intent). Smoke 200.
- [x] Config watcher: `spawn_config_watcher()` chiamato in main.rs per hot-reload
- [x] Graceful shutdown: WAL checkpoint TRUNCATE prima del drop del pool
- [x] CodeQL fix: validate plan_id > 0 in checkpoint handlers
- [x] curl test: 815 test verdi, 0 regressions. Daemon su :8421, tutti endpoint nuovi rispondono.

#### 23c: Replace stubs — DONE 2026-04-04 (PR #29)
- [x] **convergio-org**: 11 endpoint — CRUD orgs, members, orgchart, notifications (queue/list), decisions (log/query). Tabelle: ipc_orgs, ipc_org_members, notification_queue, decision_log.
- [x] **convergio-org-package**: 5 endpoint — install, list, get/:id, delete/:id, validate. Collega installer.rs, sandbox.rs, signing.rs.
- [x] **convergio-kernel**: 6 endpoint — status, classify, ask, verify, events, config. Collega engine.rs, verify.rs. Log eventi in kernel_events/kernel_verifications.
- [x] **Path param fix**: `{id}` → `:id` in 7 crate (axum 0.7 usa colon, non braces). Fix: evidence, longrunning, prompts, agents, http-bridge, depgraph.
- [x] curl test: tutti 22 nuovi endpoint rispondono 200. 815 test verdi.

#### 23d: End-to-end verification
- [x] **Env loading**: ~/.convergio/env caricato all'avvio — DONE 2026-04-04
- [x] **Auth**: Bearer token funziona — DONE 2026-04-04
- [x] **Config hot-reload**: watcher spawned, debounce 500ms, reloadable fields — DONE 2026-04-04
- [x] **WAL checkpoint**: graceful shutdown flushes WAL — DONE 2026-04-04
- [x] **DB parity**: 59 tabelle nel nuovo daemon vs 5 nel vecchio — DONE 2026-04-04
- [x] **SSE**: GET /api/ipc/stream streama ping heartbeat — DONE 2026-04-04
- [x] **Plan CRUD**: create, list, get, start, complete, checkpoint save/restore — DONE 2026-04-04
- [x] **IPC**: agents, send, messages, channels, context, status — DONE 2026-04-04
- [x] **Mesh**: peers, heartbeat, sync status — DONE 2026-04-04
- [ ] **Full route audit**: ~70 CLI endpoint, many work, some (workspace, memory) need backend — deferred
- [x] **cvg CLI**: cvg status, cvg plan list, cvg agents list funzionano
- [x] **SSE eventi reali**: DomainEventSink trait + EventBus sharing via AppContext (PR #32). plan_created flows to SSE.
- [ ] **Mesh sync**: test con peer reale — needs 2nd hardware node
- [ ] **Smoke test con vecchio CLI**: deferred until cutover (fase 22)

- Deps: tutte le fasi precedenti
- Note: Learning #14 — l'orchestratore automatico ha prodotto 10 crate con routes()→None. Questo piano lista esattamente cosa manca per ogni crate.

### Fase 24: Plan Protocol System — audit, tracking, enforcement, PM agent

**Obiettivo**: Implementare un sistema completo di plan management nel daemon:
ogni piano è auditabile, tracciato, con costi aggregati, key learnings, e un agente
PM che analizza, reporta e aggrega. Come un progetto nella vita reale.
**Motivazione**: Abbiamo costruito 23 fasi senza tracking reale — niente costi per task,
niente tempo per agente, niente aggregazione dei learnings, niente report onesti.
Il vecchio daemon aveva token_usage, audit_log, evidence gate, metrics/cost — ma dispersi.
Serve un sistema unificato che il planner, gli executor e Thor rispettano by design.
**Committente**: Roberto — "ogni piano deve essere come un progetto nella vita reale:
auditabile, chiaro, documentato, con costi e tempi tracciati".

#### 24a-24d: DONE 2026-04-04 (PR #30)
Schema, tracking API, lifecycle gates, aggregation API all implemented.
- [x] token_usage, agent_activity, plan_metadata, delegation_log tables (v4-v7)
- [x] Timestamp columns on plans/tasks/waves
- [x] 6 tracking endpoints, 4 aggregation endpoints
- [x] 5 lifecycle gates (Import, Start, Test, Evidence, Validator)
- [x] 825 tests pass. Smoke tested.

**Remaining (24e-24f)**: PM triggers, protocol enforcement — deferred to when agent runtime is mature.

#### ORIGINAL 24a: Schema — tabelle tracking e audit (convergio-orchestrator)

Le tabelle `plans`, `tasks`, `waves` esistono. Mancano le tabelle di tracking.

- [x] **token_usage**: tracking granulare per chiamata LLM
  ```
  id, plan_id, wave_id, task_id, agent, model, input_tokens, output_tokens,
  cost_usd, execution_host, created_at
  ```
  Indici: (plan_id), (agent), (model), (created_at DESC)
- [x] **agent_activity**: chi ha lavorato su cosa, per quanto, con quale esito
  ```
  id, agent_id, agent_type, plan_id, task_id, action, status, model,
  tokens_in, tokens_out, cost_usd, started_at, completed_at, duration_s,
  host, exit_reason, metadata_json, created_at
  ```
- [x] **plan_metadata**: campi auditabili per ogni piano
  ```
  plan_id (PK FK), objective, motivation, requester, created_by,
  approved_by, key_learnings_json, report_json, closed_at
  ```
- [x] **delegation_log**: tracking delegazioni a peer/agenti
  ```
  id, plan_id, task_id, peer_name, agent, delegated_at, completed_at,
  status, cost_usd, tokens_total
  ```
- [x] Aggiungere a `tasks`: `validated_at`, `validator_agent`, `duration_minutes`
- [x] Aggiungere a `plans`: `started_at`, `completed_at`, `cancelled_at`
- [x] Aggiungere a `waves`: `completed_at`, `cancelled_at`

#### 24b: API tracking — endpoint per registrare costi e attività

- [x] `POST /api/tracking/tokens` — ogni chiamata LLM registra tokens (agent, model, cost, task context)
- [x] `POST /api/tracking/agent-activity` — upsert attività agente (inizio, fine, costo, esito)
- [x] `POST /api/plan-db/metadata` — scrivere/aggiornare objective, motivation, requester, learnings
- [x] `GET /api/plan-db/metadata/:plan_id` — leggere metadati piano
- [x] `POST /api/plan-db/report` — scrivere report finale di una fase/piano
- [ ] Wiring: il runtime agente chiama automaticamente tracking/tokens ad ogni completamento inferenza
- [ ] Wiring: on_start/on_shutdown dell'agente chiama agent-activity

#### 24c: Lifecycle gates — DONE (PR #30)

- [x] **ImportGate**: non puoi aggiungere task a un piano non in draft/todo/approved
- [ ] **ReviewGate**: non puoi startare un piano senza review approvata — deferred (no review table yet)
- [x] **StartGate**: non puoi startare senza almeno 1 task
- [x] **TestGate**: task non può passare a `submitted` senza evidence type=test_pass
- [x] **ValidatorGate**: task non può passare a `done` senza validation verdict positivo
- [x] **EvidenceGate**: task non può passare a `submitted` senza almeno 1 record in task_evidence
- [ ] Ogni violazione di gate → errore 409 — gates implementate come funzioni, non ancora wired nei route handlers
- [x] I gate sono implementati come funzioni in gates.rs, check_task_transition() orchestrates

#### 24d: Aggregation API — DONE (PR #30)

- [x] `GET /api/metrics/cost?days=N` — costo per modello e per giorno
- [x] `GET /api/metrics/summary` — totale runs, costo totale, distribuzione status
- [ ] `GET /api/metrics/run/:id` — metriche singola esecuzione — deferred
- [x] `GET /api/audit/project/:project_id` — report auditabile completo del progetto:
  piani, task, agenti, costi, durate, evidence, learnings, PR links
- [ ] `GET /api/plan-db/report/:plan_id` — report finale del piano con tutti i campi del template:
  obiettivo, motivazione, committente, cosa fatto, cosa NON fatto, test evidence,
  key learnings, impatto su fasi successive, costo totale, tempo totale, agenti coinvolti
- [ ] Aggregazione key learnings: `GET /api/learnings?project=X` —
  tutti i learnings da tutti i piani di un progetto, aggregati e deduplicati

#### 24e: Agente PM (Program/Project Manager)

Il PM è un ruolo strutturale dell'organizzazione, come il CEO.
Ogni org DEVE avere un PM, esattamente come ha un CEO, un CTO, un designer, etc.
Il PM non scrive codice — analizza, reporta, aggrega, tiene la governance.
Quando `cvg org create` provisiona un'org, il PM viene creato automaticamente
insieme al CEO e agli altri ruoli fondamentali. Non è opzionale.

- [x] **Ruolo strutturale**: il PM è nel blueprint di ogni org (come ceo, cto, etc.)
  `cvg org create` lo provisiona automaticamente — non si può creare un'org senza PM
- [x] **Definizione agente**: `convergio-pm` nel seed catalog, role=project_manager, model_tier=t3 — PR #28 mergiata 2026-04-04
- [x] **Prompt professionale**: `ConvergioPlatform/claude-config/agents/core_utility/convergio-pm.md`
  Skills analitiche (cost breakdown, duration tracking, evidence gaps, failure rate, cost forecast)
  + comunicazione executive (tables over prose, numbers first, anomaly flagging, weekly digest)
- [ ] **Trigger automatici**: wave/plan close → PM auto-analyze — deferred (needs event subscription wiring)
- [x] **Endpoint PM** (PR #35):
  - `POST /api/pm/analyze/:plan_id` — cost breakdown, evidence gaps, completion %
  - `GET /api/pm/digest` — weekly digest (plans, cost, tokens, agents)
  - `GET /api/pm/learnings` — aggregated key learnings
  - `GET /api/pm/cost-forecast` — cost projection
- [x] **Output del PM**: report saved in plan_metadata.report_json via POST /api/plan-db/report

#### 24f: Protocol enforcement — DONE (PR #35)

- [x] Plan creation auto-creates plan_metadata when objective/motivation/requester provided
- [x] Task status transitions validated by lifecycle gates (gates.rs → task_routes.rs)
- [ ] L'executor DEVE chiamare tracking/tokens per ogni inferenza — needs agent runtime wiring
- [ ] Thor checks key_learnings not empty at plan closure — deferred

- Deps: Fase 23 (daemon funzionante end-to-end)
- Note: Learning #13-14. Il vecchio workflow aveva i pezzi giusti ma dispersi.
  Questo li unifica in un protocollo che tutti gli attori rispettano.
  Il PM è l'agente che tiene tutto insieme — l'auditor interno di ogni org.

### Fase 25: Eliminare script — tutto dentro il daemon

Gli script in scripts/ sono workaround perché convergio non era operativo.
Ora che il daemon gira, ogni script deve diventare un comando nativo.

- [ ] `orchestrator.sh` → `cvg plan execute <id>` — il daemon orchestra wave, spawna agenti, monitora, mergia
- [ ] `launch-fase.sh` → `cvg agent spawn <name> --task <id> --worktree` — runtime crea worktree, lancia agente
- [ ] `chain-fasi.sh` → wave ordering nell'orchestrator — già previsto nell'architettura
- [ ] `cutover.sh` → `cvg admin cutover --from-port 8420` — il daemon migra se stesso
- [ ] `frontend-orchestrator.sh` → `cvg plan create --spec file.md` + il daemon fa tutto
- [ ] Dopo migrazione: eliminare orchestrator.sh, launch-fase.sh, chain-fasi.sh, frontend-orchestrator.sh
- [ ] Mantenere solo: cutover.sh (bootstrap, serve prima che il daemon esista)
- Deps: Fase 24 (workflow nativo)
- Note: Se serve uno script bash per far funzionare convergio, convergio non è finito.

### Fase 26: Self-hosting — convergio costruisce convergio

Il test definitivo: convergio usa se stesso per pianificare, eseguire e validare il proprio sviluppo.

- [ ] Creare piano via daemon: `cvg plan create "Convergio Frontend" --spec ~/Desktop/FRONTEND-SPEC.md`
- [ ] Il planner scompone in wave/task e assegna agenti (sara-ux, jony, baccio, nasra)
- [ ] Gli agenti lavorano in worktree isolati, il runtime li monitora
- [ ] Thor valida ogni task con evidence (curl proof, screenshot, test output)
- [ ] Il sistema crea PR, aspetta CI, mergia — tutto senza intervento umano
- [ ] L'utente osserva dalla UI — vede agenti lavorare in real-time
- [ ] Se un agente muore, il reaper rileva e il runtime ne spawna un altro
- [ ] Se il contesto si riempie, l'agente checkpointa e un nuovo agente riprende
- Deps: Fase 25 (script eliminati), Fase 23 (daemon funzionante), Frontend
- Note: Questo è il momento in cui convergio diventa reale. Se non riesce a costruire la propria UI, non è pronto.

### Fase 27: Migrazione operativa completa da ConvergioPlatform

Tutto il valore operativo del vecchio repo che non è stato ancora portato.
Sorgente: /Users/Roberdan/GitHub/ConvergioPlatform/claude-config/

#### 27a: Rules + Git hooks
- [ ] Migrare claude-config/rules/best-practices.md → convergio rules (nel daemon o CLAUDE.md)
- [ ] Migrare claude-config/rules/hard-enforcement.md → hook enforced nel nuovo repo
- [ ] Migrare git hooks: pre-commit (MainGuard, FileSizeGuard, SecretScan, SqliteBlock, CommitLint)
- [ ] Migrare git hooks: commit-msg (conventional commit enforcement)
- [ ] Creare .claude/settings.json nel nuovo repo con gli stessi hook Claude (C1-C10)

#### 27b: Skills + Commands — DONE 2026-04-04 (PR #33)
- [x] 8 skill prompts seeded in prompt_templates
- [x] Workflow pipeline (solve→planner→execute→thor) in prompt_pipelines
- [ ] Command files as cvg commands (deferred — skills are Claude Code skills, not daemon commands)

#### 27c: Agent definitions (le 9 organizzazioni)
- [ ] Migrare 70 agent definitions da claude-config/agents/ (10 categorie)
- [ ] Ogni agente diventa: TOML spec + prompt .md nel formato org-as-package
- [ ] Seed data: `cvg org install convergio-default` installa tutte le org
- [ ] Mapping modello: ogni agente ha il suo model tier (t1-t4) e budget

#### 27d: Config + reference + data — DONE 2026-04-04 (PR #34)
- [x] models.yaml, orchestrator.yaml, notifications.conf → claude-config/config/
- [x] plan-spec-schema.json, skill-frontmatter.schema.json → claude-config/schemas/
- [x] 5 key reference docs → claude-config/reference/
- [ ] thor-audit.jsonl seed data (deferred)

#### 27e: Hooks Claude operativi (URGENTE — nuovo repo ha 1 hook, vecchio ne aveva 18+)
- [ ] Migrare .claude/settings.json completo (permissions allow/deny + tutti gli hook)
- [ ] **PreCompact hook** (CRITICO): salva stato nel tracker prima della compattazione. Senza questo gli agenti perdono contesto silenziosamente. Collegare al checkpoint/resume di Fase 15.
- [ ] **Context exhaustion detection**: rileva contesto al 80%, salva checkpoint, aggiorna tracker, lancia nuovo agente fresco. È il LongRunnable.checkpoint()+resume() per agenti Claude stessi.
- [ ] **PreToolUse**: MainGuard, BlockBranchCreation, ThorGateGuard, IPC inject, pre-tool-guard (secret scan)
- [ ] **PostToolUse**: FileSizeGuard (250 righe, BLOCKING), Rust wiring check, cargo check post-edit
- [ ] **SubagentStart**: registra IPC, preflight auth, dirty check, agent identity
- [ ] **SubagentStop**: evidence gate, auto-submit task
- [ ] **Notification**: polling inbox messaggi inter-agente
- [ ] **Permissions**: whitelist (cargo, git read, curl, cvg), deny (rm -rf, force push, sqlite3, secrets)
- [ ] Ogni hook diventa: hook .claude/settings.json nel nuovo repo, o funzionalità nativa daemon

#### 27f: Script operativi critici
- [ ] Valutare i 100+ script in claude-config/scripts/
- [ ] Classificare: da migrare (copilot-worker, thor-validate, worktree-*) vs obsoleti
- [ ] Quelli da migrare diventano comandi cvg o funzionalità daemon
- [ ] Quelli obsoleti si archiviano

- Deps: Fase 24 (workflow nativo), Fase 23 (daemon funzionante)
- Note: Questo è il DNA operativo di ConvergioPlatform. Senza questo, convergio ha l'infrastruttura ma non sa come usarla.

### Fase 28: Voice + Telegram + external extensions

- [ ] convergio-voice: completare STT/TTS con Whisper reale (non stub)
- [ ] Telegram bot: notifiche, comandi, voice routing
- [ ] OpenClaw bridge: registrare come HTTP extension esterna
- [ ] Evolution bridge: registrare come HTTP extension esterna
- [ ] Test: voice command → daemon action, Telegram message → notification
- Deps: Fase 23 (daemon funzionante), Fase 14 (HTTP bridge)
- Note: Queste sono extension opzionali ma importanti per l'uso quotidiano.

### Fase 29a: CONSTITUTION.md + README + Licensing — DONE (PR #31)

- [x] CONSTITUTION.md creato nella root con 9 regole + 16 learnings (14 originali + 2 da audit)
- [x] README.md creato: architettura, quick start, repo layout, principi, licenza
- [x] LICENSE presente (Convergio Community License)
- [ ] Copiare CONSTITUTION.md anche in convergio-frontend
- [ ] CLAUDE.md: aggiungere `Read CONSTITUTION.md` come prima istruzione

---

### WAVE G — Delegation Pipeline (il gap critico: da API passivo a sistema che AGISCE)

Learning #15: 26 crate funzionano in isolamento ma il core use case non funziona.
Il daemon è un API layer passivo — registra, traccia, serve dati. Non agisce.
Queste fasi lo trasformano in un sistema che spawna agenti, sincronizza dati, copia file tra nodi.

### Fase 30: Real-time DB sync (mesh background loop)

**Obiettivo**: Sostituire il batch export/import con sync continuo in background tra nodi.
**Motivazione**: Oggi `sync_table_with_peer()` esiste ma nessun loop la chiama. Il mesh ha le tabelle
e le API ma nessun background task. Un nodo non vede i cambiamenti dell'altro fino a export manuale.
**Committente**: Roberto — audit 04 Aprile 2026.
**Deps**: mesh✅, db✅, telemetry✅, longrunning✅ (heartbeat pattern)

#### Task
- [ ] Background sync loop: `tokio::spawn` che chiama `sync_table_with_peer()` per ogni peer/tabella ad intervallo configurabile (default 30s, env `CONVERGIO_SYNC_INTERVAL_SECS` già previsto)
- [ ] Tabelle da sincronizzare: plans, tasks, waves, agents, token_usage, agent_activity (dichiarate in `SYNC_TABLES` in mesh/types.rs — verificare che includa le nuove tabelle fase 24)
- [ ] WAL-based change detection: usare `updated_at` column (già presente) per delta sync incrementale
- [ ] Conflict resolution: LWW (last-write-wins) con node priority configurabile. Loggare conflitti in `_sync_conflicts` (tabella già esiste)
- [ ] Sync health monitoring: detect sync lag, alert if >30s behind (via observatory anomaly detection)
- [ ] SSE event per sync: `SyncCompleted { peer, tables, sent, received, latency_ms }`
- [ ] Wire il loop in `MeshExtension::on_start()` — il sync parte automaticamente con il daemon
- [ ] API: `GET /api/mesh/sync/status` (per-peer lag, last sync, failures), `POST /api/mesh/sync/force` (trigger sync immediato)
- [ ] Integration test: 2 pool in-memory, sync bidirezionale, verifica convergenza

#### Report finale (compilato a chiusura)
- **Stato**: —
- **PR**: —

### Fase 31: File transport layer

**Obiettivo**: rsync wrapper per copiare repository (inclusi .env e file non-git) tra nodi.
**Motivazione**: La delegation richiede che il nodo remoto abbia il codice. Git clone non basta:
serve anche .env, .claude/, config locali. Il vecchio DelegateEngine usava rsync — serve equivalente.
**Committente**: Roberto — audit 04 Aprile 2026.
**Deps**: mesh✅ (peer resolution), security✅ (SSH key management)

#### Task
- [ ] Crate `convergio-mesh` (estensione) o modulo `transport_file.rs` dentro mesh
- [ ] `rsync_copy(src_path, peer_addr, dest_path, exclude_patterns)` → async wrapper su `tokio::process::Command` per rsync via SSH
- [ ] Pre-copy validation: SSH connectivity check, disk space check (via `df` remoto), path exists
- [ ] Post-copy verification: file count + total size comparison (rsync `--stats` parsing)
- [ ] Exclude patterns configurabili: default esclude `.git/objects`, `target/`, `node_modules/`
- [ ] Include patterns obbligatori: `.env`, `.claude/`, `config/` — mai persi nel trasferimento
- [ ] Progress reporting via SSE: `CopyProgress { id, percent, bytes_sent, speed }`
- [ ] API: `POST /api/transport/copy` (start copy job), `GET /api/transport/status/:id` (poll status)
- [ ] Integration test: copia directory locale → directory locale (simula remoto), verifica contenuti

#### Report finale (compilato a chiusura)
- **Stato**: —
- **PR**: —

### Fase 32: Agent spawning — locale e remoto, multi-model

**Obiettivo**: Spawning reale di agenti (non solo DB insert). L'utente sceglie il modello O lascia che il router decida.
**Motivazione**: L'agent-runtime ha allocation/delegation/heartbeat/reaper ma non spawna agenti realmente.
`allocator.rs` inserisce in DB, ma nessun processo viene creato. Il daemon deve poter lanciare
agenti su nodo locale o remoto, scegliendo il backend ottimale per il task.
**Committente**: Roberto — "non sempre Claude, dobbiamo ottimizzare i token"
**Deps**: mesh✅, agent-runtime✅, transport (fase 31), prompts✅, inference✅

#### Backend di esecuzione (NON solo Claude)
Il **convergio-inference router** (Fase 11, già implementato) decide il backend:
- **t1 (Opus)**: task complessi — architettura, debug cross-crate, planning
- **t2 (Sonnet)**: task medi — implement feature, code review, refactor
- **t3 (Haiku)**: task semplici — rename, format, doc update, test writing
- **t4 (Local Qwen/MLX)**: task meccanici — grep, count, schema check
- **Budget override**: se il budget org è quasi finito → downgrade automatico
- **User override**: `cvg delegate --model claude-opus-4-6` forza il modello

#### Modalità di spawning
| Backend | Come invoca | Quando |
|---------|------------|--------|
| Claude Code CLI | `timeout N claude --dangerously-skip-permissions -p "Leggi <file>"` | t1/t2, task con file access |
| gh Copilot | `gh copilot --model X` dentro worktree | Task meccanici ben definiti |
| API diretta | POST a Anthropic/OpenAI/Ollama API | Task senza file access (analisi, classificazione) |
| Script | Script bash/python deterministico | Task ripetitivi (lint, format, migrate) |

**ATTENZIONE Learning #7**: `claude -p` con prompt >3000 chars causa hang silenzioso.
Pattern funzionante: prompt corto che dice di LEGGERE un file con le istruzioni complete.

#### Task
- [ ] `spawn_local_agent(agent_spec)` — crea worktree, usa inference router per scegliere backend, lancia processo con env vars (CONVERGIO_AGENT_NAME, CONVERGIO_ORG, CONVERGIO_TASK_ID, CONVERGIO_DAEMON_URL)
- [ ] `spawn_remote_agent(peer_addr, agent_spec)` — POST al daemon remoto che chiama spawn_local_agent
- [ ] Inference routing at spawn: `convergio-inference` decide t1/t2/t3/t4, poi il spawner sceglie il backend appropriato
- [ ] User model override: `--model claude-opus-4-6` bypassa il router
- [ ] Agent spec: nome, ruolo, org, model (optional), budget, prompt_ref, task_id, worktree path
- [ ] Prompt injection at spawn: istruzioni in FILE (non inline), l'agente le legge al primo turno
- [ ] Heartbeat cross-node: l'agente remoto manda heartbeat al daemon locale via mesh
- [ ] Auto-recovery: se heartbeat manca per >5min, reaper rileva, notifica orchestratore
- [ ] Process lifecycle: spawning → running → completed/failed/timeout. Tracked in art_agents.
- [ ] API: `POST /api/agents/spawn` (locale), `POST /api/agents/spawn-remote` (remoto), `GET /api/agents/:id/logs`
- [ ] Integration test: spawn locale con Haiku (economico), verifica heartbeat e cleanup

#### Report finale (compilato a chiusura)
- **Stato**: —
- **PR**: —

### Fase 33: Telegram notification system

**Obiettivo**: Inviare notifiche Telegram per eventi importanti del sistema.
**Motivazione**: notification_queue e notification_deliveries esistono in convergio-org.
I tipi ci sono. Manca l'HTTP client che parla con Telegram Bot API. Roberto vuole vedere
"Elena ha completato il task" sul telefono, non nel terminale.
**Committente**: Roberto — audit 04 Aprile 2026.
**Deps**: org✅ (notification tables), ipc✅ (domain events), security✅ (bot token storage)

#### Task
- [ ] Telegram Bot API client: `reqwest` async, `sendMessage`, `sendDocument` (per report allegati)
- [ ] Notification types: task_done, plan_done, error, budget_alert, delegation_complete, agent_died
- [ ] Message formatting con nomi umani: "Elena (Legal Corp) ha completato 'Review contratto' — costo $0.47, durata 12min"
- [ ] Per-org notification preferences: which events, which Telegram chat_id. Tabella `notification_preferences`.
- [ ] Delivery tracking: notification_deliveries aggiornato con sent_at, delivery_id, error se fallisce
- [ ] Rate limiting: max 30 msg/s per bot (Telegram limit). Queue con backpressure.
- [ ] Domain event subscription: on_event(TaskCompleted) → format → send Telegram
- [ ] API: `POST /api/notify/telegram/send` (manual), `GET /api/notify/preferences` (CRUD), `POST /api/notify/preferences`
- [ ] Config: `CONVERGIO_TELEGRAM_BOT_TOKEN` env var, `CONVERGIO_TELEGRAM_DEFAULT_CHAT_ID` per fallback
- [ ] Integration test: mock Telegram API (wiremock), verify message format and delivery tracking

#### Report finale (compilato a chiusura)
- **Stato**: —
- **PR**: —

### Fase 34: Delegation orchestrator (the glue)

**Obiettivo**: Un singolo comando che orchestra l'intero pipeline di delegazione.
**Motivazione**: Le fasi 30-33 costruiscono i pezzi. Questa fase li compone nel workflow:
`cvg delegate <project> --to <node>` → copia file → setup remoto → spawn agent → monitor → sync back → notify.
Senza questo, l'utente deve orchestrare manualmente 5 step.
**Committente**: Roberto — audit 04 Aprile 2026.
**Deps**: mesh sync (30), file transport (31), remote spawn (32), Telegram (33), orchestrator✅

#### Task
- [ ] `DelegationPipeline` struct: state machine con step (Preparing, Copying, Spawning, Running, SyncingBack, Completed, Failed)
- [ ] Step 1 — Prepare: verify peer online (heartbeat), check disk space, resolve best addr
- [ ] Step 2 — Copy: rsync project to remote (fase 31 API), wait for completion
- [ ] Step 3 — Setup: create worktree on remote, install dependencies if needed
- [ ] Step 4 — Spawn: launch agent on remote (fase 32 API), propagate identity/budget/prompt
- [ ] Step 5 — Monitor: heartbeat tracking, budget guard, progress via SSE
- [ ] Step 6 — Sync back: when agent completes, rsync results back to local
- [ ] Step 7 — Verify: check results (git diff, test output), update task status
- [ ] Step 8 — Notify: Telegram notification (fase 33) with summary
- [ ] Rollback on failure: if any step fails, cleanup partial state on remote (remove worktree, kill agent)
- [ ] Real-time progress via SSE: `DelegationProgress { id, step, percent, detail }`
- [ ] API: `POST /api/delegate` (start pipeline), `GET /api/delegate/:id` (status), `POST /api/delegate/:id/cancel`
- [ ] CLI: `cvg delegate <project> --to <node> [--org <org>] [--agent <name>]`
- [ ] Integration test: delegate to localhost (self-node), verify full pipeline

#### Report finale (compilato a chiusura)
- **Stato**: —
- **PR**: —

### Fase 35: End-to-end integration test

**Obiettivo**: Prova che il sistema funziona davvero. Non unit test, non curl — un test reale.
**Motivazione**: Learning #13, #14, #15: abbiamo dichiarato "done" troppe volte senza evidence E2E.
Questa fase è il "it actually works" test per l'intera delegation pipeline.
**Committente**: Roberto — audit 04 Aprile 2026.
**Deps**: Fase 34 (delegation orchestrator)

#### Task
- [ ] Test scenario: delegate un progetto semplice (hello-world Rust) a localhost (simula nodo remoto con porta diversa)
- [ ] Verify: file copiati, worktree creato, agent spawnato (mock claude o script semplice)
- [ ] Verify: task completato, risultati sincronizzati back, notifica inviata
- [ ] Verify: cleanup — worktree rimosso, agent deregistrato, delegation closed
- [ ] Metriche: tempo totale pipeline, bytes trasferiti, latenza sync
- [ ] Questo test diventa il gate per dichiarare "delegation pipeline works"
- [ ] Aggiungere a CI come integration test (richiede 2 daemon instance)

#### Report finale (compilato a chiusura)
- **Stato**: —
- **PR**: —

### Fase 32b: Agent→Plan lifecycle wiring (CRITICO)

**Obiettivo**: Quando un agente finisce, il piano si aggiorna automaticamente.
**Motivazione**: PROBLEMA ALLA RADICE — gli agenti lavorano, committano, il monitor fa push+PR,
ma il piano resta `todo` per sempre. Nessuno chiama `/api/plan-db/complete`. Il sistema SEMBRA
non funzionare anche quando funziona. Roberto lo ha visto nella UI: tutti i piani "queued" anche
dopo che il lavoro è stato fatto e mergiato. Questo è lo stesso tipo di bug dei Learning #13-14
(crate che compilano ma non contribuiscono al sistema).
**Committente**: Roberto — "è un problema alla radice di convergio"
**Deps**: Fase 32 (spawning), Fase 24c (lifecycle gates)

#### Il loop che DEVE chiudersi
```
POST /api/agents/spawn (con task_id e plan_id)
  → agent lavora nel worktree
  → agent committa
  → monitor rileva exit
  → monitor pusha + crea PR
  → monitor aggiorna agent stage → stopped
  → [MANCA] monitor aggiorna task status → submitted
  → [MANCA] monitor aggiorna plan progress (tasks_done++)
  → [MANCA] se tutti i task del piano sono done → plan status → done
  → [MANCA] emette DomainEvent (task_completed, plan_completed)
  → [MANCA] SSE notifica la UI in tempo reale
  → [MANCA] Telegram notifica Roberto
```

#### Task
- [ ] `spawn_monitor.rs`: dopo push+PR, chiama `POST /api/plan-db/task/update` con `status=submitted`
- [ ] `spawn_monitor.rs`: se task_id presente, aggiorna il task nel piano
- [ ] `spawn_monitor.rs`: emetti DomainEvent::TaskCompleted via EventBus (serve accesso al sink)
- [ ] Orchestrator reactor: quando task_completed arriva, conta task rimanenti → se zero → wave_done → plan_done
- [ ] Plan auto-progression: wave_done automatico quando tutti i task della wave sono done
- [ ] Telegram: notifica quando piano completo (se CONVERGIO_TELEGRAM_BOT_TOKEN è set)
- [ ] Test: spawna agente con task_id → verifica che il piano si aggiorna dopo completion
- [ ] Fix manuale: aggiorna piano #3 (launchd) a `done` — il lavoro è stato fatto e mergiato

### Fase 32c: Planner E2E — piani di cui fidarsi (CRITICO)

**Obiettivo**: Il planner produce piani COMPLETI che coprono il loop end-to-end, non liste di task sconnesse.
**Motivazione**: Roberto: "voglio che il planner sia veramente in grado di pianificare end2end
e di costruire un piano totale di cui io possa fidarmi". Oggi il planner (sia skill Claude che API)
crea task ma non verifica che:
- Ogni task abbia un input chiaro e un output verificabile
- Il wiring tra task sia esplicito (output di A → input di B)
- Il test E2E sia incluso come ultimo task di ogni wave
- Il loop si chiuda (chi aggiorna lo stato? chi notifica? chi pulisce?)
**Committente**: Roberto
**Deps**: Fase 32b (lifecycle wiring), Fase 24c (gates)

#### Cosa deve fare il planner PRIMA di creare i task
Per OGNI task nel piano, il planner DEVE specificare:
1. **Input**: cosa serve per iniziare (file, dati, risultato di un task precedente)
2. **Output**: cosa produce (file, commit, endpoint, test)
3. **Verifica**: come Thor valida che è fatto (cargo test? curl? file exists?)
4. **Wiring**: chi consuma il mio output? il loop si chiude?

#### Task
- [ ] Template di piano obbligatorio: ogni piano creato via API DEVE avere objective, motivation, requester (enforced dalla API, non opzionale)
- [ ] Ogni task nel piano DEVE avere: titolo, description con acceptance criteria, agente assegnato, tier
- [ ] L'ultimo task di ogni wave è SEMPRE un integration test (enforced dal planner)
- [ ] Il planner aggiunge automaticamente task di wiring: "verifica che X è visibile nella UI", "verifica che il DB riflette lo stato"
- [ ] API: POST /api/plan-db/validate — verifica che il piano sia completo (tutti i campi, loop chiuso, test incluso)
- [ ] Se il piano non passa la validazione → errore 400 con lista dei campi mancanti
- [ ] Il planner deve leggere Regola 10 (loop E2E) e le 4 domande obbligatorie PRIMA di creare task

### Fase 32d: Thor a livello piano — challenger completo

**Obiettivo**: Thor non valida solo wave, ma l'intero piano PRIMA dell'esecuzione e DOPO il completamento.
**Motivazione**: Roberto: "thor dovrebbe anche essere a livello di piano complessivo, un challenger
ogni volta che vede che il planner non aveva pensato a qualcosa". Oggi Thor è invocato solo su
`wave_needs_validation` — non vede il piano nel suo complesso.
**Committente**: Roberto
**Deps**: Fase 32c (planner E2E), Fase 32b (lifecycle wiring)

#### Thor pre-execution (challenger del piano)
Quando un piano passa da `approved` → `in_progress`, Thor fa una review del piano completo:
1. **Completezza**: ogni task ha input/output/verifica? Mancano task di wiring?
2. **Realismo**: il budget è sufficiente per i task previsti? (basato su storico costi)
3. **Rischi**: ci sono dipendenze circolari? Task senza agente? Wave senza test?
4. **Loop E2E**: il piano include test che verificano il loop dall'inizio alla fine?
5. **Learnings**: i learnings passati sono stati considerati? (es: se il piano tocca auth, Learning #13 dice di testare E2E)

Se Thor trova problemi → piano resta `approved`, Thor emette feedback, il planner corregge.
Solo quando Thor approva → piano va in `in_progress`.

#### Thor post-execution (validazione finale)
Quando tutti i task sono `submitted`:
1. **Evidence check**: ogni task ha commit, test, PR?
2. **Integration check**: il sistema funziona E2E? (curl test, UI check)
3. **Regression check**: i test del workspace passano tutti?
4. **Cost audit**: il costo totale è ragionevole vs budget?
5. **Learning extraction**: cosa abbiamo imparato? Il PM compila il report.

Se Thor non approva → piano resta `submitted`, task problematici tornano `in_progress`.
Solo quando Thor approva → piano va in `done`.

#### Task
- [ ] `POST /api/plan-db/review` — Thor review pre-execution. Prende plan_id, ritorna verdict + findings
- [ ] `POST /api/plan-db/validate-completion` — Thor review post-execution. Verifica evidence, integration, regression
- [ ] Gate: plan `approved` → `in_progress` richiede Thor pre-review positiva
- [ ] Gate: plan `submitted` → `done` richiede Thor post-review positiva
- [ ] Thor legge learnings passati (da plan_metadata.key_learnings_json) e verifica che siano considerati
- [ ] Thor produce report strutturato: {verdict, findings[], recommendations[], cost_assessment}
- [ ] Thor report salvato in plan_metadata.report_json
- [ ] Se Thor trova > 3 problemi critici → piano bloccato, notifica Roberto
- [ ] Test: crea piano incompleto (senza test E2E) → Thor lo rifiuta

### Fase 23e: Depgraph wiring in main.rs

**Obiettivo**: Registrare DepgraphExtension in main.rs con i manifest di tutte le extension.
**Motivazione**: Il crate compila, ha 30 test, implementa Extension con routes reali (/api/depgraph, /api/capabilities, /api/openapi) — ma non è wired nel daemon perché il constructor richiede Vec<Manifest>.
**Committente**: Audit 04 Aprile 2026.
**Deps**: tutte le extension registrate✅

#### Task
- [ ] In main.rs, dopo `register_extensions()`, raccogliere `ext.manifest()` da ogni extension
- [ ] Creare `DepgraphExtension::new(manifests)` e aggiungerlo alla lista
- [ ] Verificare: `curl http://localhost:8420/api/capabilities` ritorna lista moduli
- [ ] Verificare: `curl http://localhost:8420/api/depgraph` ritorna grafo JSON
- [ ] Verificare: startup validation passes (nessun ciclo, deps soddisfatte)

#### Report finale (compilato a chiusura)
- **Stato**: —
- **PR**: —

### WAVE H — Operations & Polish (dopo Wave G)

### Fase 36b: Inference reale — chiamate a modelli locali e API

**Obiettivo**: Il router di inference (Fase 11) CHIAMA veramente i modelli, non echo.
**Motivazione**: Oggi `router.rs` ritorna `"[routed to t2] echo"`. Deve chiamare Ollama, MLX, o API cloud.
**Committente**: Roberto — "possiamo usare modelli locali come in ConvergioPlatform"

#### Task
- [ ] Backend Ollama: HTTP client che chiama `POST http://localhost:11434/api/generate`
- [ ] Backend MLX: subprocess che invoca `mlx-lm generate` (come TTS già fa per audio)
- [ ] Backend API cloud: reqwest client verso Anthropic API (header x-api-key da env)
- [ ] Il router decide il backend in base al tier: t4→Ollama/MLX, t3→Haiku API, t2→Sonnet API, t1→Opus API
- [ ] Budget guard: se budget esaurito, rifiuta o downgrade (logica già in budget.rs)
- [ ] Test: inference reale con Ollama locale (richiede Ollama installato)
- [ ] Streaming response: SSE per risposte lunghe (non bloccare su completion intera)

### Fase 36c: STT Whisper — completare speech-to-text

**Obiettivo**: `whisper.rs` funziona davvero con trascrizione locale.
**Motivazione**: `transcribe_local()` e `transcribe_api()` ritornano errori placeholder.
**Deps**: convergio-voice✅

#### Task
- [ ] Implementare `transcribe_local()` via `whisper-rs` o subprocess `mlx-whisper`
- [ ] Implementare `transcribe_api()` via OpenAI Whisper API (fallback)
- [ ] Test con file WAV reale
- [ ] Wire in kernel routes: POST /api/kernel/transcribe

### Fase 37b: Node capability registry — nodi specializzati nel mesh

**Obiettivo**: Ogni nodo dichiara le sue capability (GPU, voce, compute, storage). Il mesh routing le usa.
**Motivazione**: Roberto vuole che kernel/voce/Telegram siano ruoli di nodi specifici.
Oggi tutti i nodi sono identici — non puoi dire "manda questo al nodo con GPU".
**Committente**: Roberto — "kernel e la voce e telegram possono essere ruoli specifici di nodi"

#### Task
- [ ] `NodeCapabilities` struct: gpu (bool, vram_gb), voice (bool), compute_cores, storage_gb, roles (Vec<String>)
- [ ] Tabella `mesh_node_capabilities`: node_name, capabilities_json, updated_at
- [ ] Ogni nodo pubblica le sue capability all'avvio: `POST /api/mesh/capabilities`
- [ ] Il mesh router usa le capability per decidere: "task voce → nodo con voice=true"
- [ ] Capability-aware delegation: `cvg delegate --requires gpu,voice`
- [ ] API: GET /api/mesh/nodes (include capability), GET /api/mesh/nodes/:name/capabilities
- [ ] Degradazione: se nodo con capability richiesta è offline, fallback o errore chiaro

### Fase 38b: macOS menu bar — daemon status icon

**Obiettivo**: Icona nella barra menu macOS che mostra: stato daemon, nodo, agenti attivi, costo.
**Motivazione**: Roberto vuole sapere a colpo d'occhio se il daemon gira senza aprire terminale.
**Committente**: Roberto — "un'icona nelle icone di sistema che indichi se sta girando"

#### Task
- [ ] App SwiftUI minimale (rumps/py o nativa Swift) che fa polling a `http://localhost:8420/api/health`
- [ ] Icona verde (running), gialla (degraded), rossa (down), grigia (not running)
- [ ] Menu dropdown: versione, uptime, nodo, agenti attivi, costo oggi, ultimo evento
- [ ] Click "Open Dashboard" → apre `http://localhost:3000` nel browser
- [ ] Click "Restart Daemon" → kill + relaunch
- [ ] Click "View Logs" → apre Console.app filtrato per convergio
- [ ] Binary compilato una volta sola — no Xcode ogni volta
- [ ] Distribuibile come .app o installabile con `brew install convergio-menubar`

### Fase 38c: Daemon auto-start + launchd + firewall

**Obiettivo**: Il daemon parte automaticamente al login e non chiede permessi firewall ogni volta.
**Motivazione**: Oggi il daemon va lanciato manualmente e ogni ricompilazione chiede permessi macOS.
**Committente**: Roberto — "non dover intervenire fisicamente sulla macchina"

#### Task
- [ ] `com.convergio.daemon.plist` per launchd: auto-start al login, restart on crash
- [ ] `scripts/install-service.sh`: copia plist, carica con `launchctl load`
- [ ] Code signing del binary con certificato developer (evita firewall popup)
- [ ] Oppure: `socketfilterfw --add` per whitelist permanente del binary
- [ ] Script `scripts/add-mesh-node.sh <hostname>`: SSH al nodo, copia binary, installa plist, configura firewall, registra nel mesh
- [ ] Zero-touch node addition: nessun intervento fisico sul nodo remoto
- [ ] Healthcheck: launchd verifica che /api/health risponda, restart se no

### Fase 39b: Progetti non-codice — report, documenti, business

**Obiettivo**: Convergio gestisce QUALSIASI tipo di progetto, non solo codice.
**Motivazione**: Nelle specifiche iniziali convergio è un assistente di business — report, analisi, documenti legali, marketing, non solo Rust/TypeScript.
**Committente**: Roberto — "qualsiasi tipo di progetto sia esso applicazioni, codice o report"

#### Task
- [ ] Template progetto per: report (markdown), business document (LaTeX/PDF), analisi dati (Python notebook), marketing plan
- [ ] `cvg project init --type report` genera struttura per documenti non-codice
- [ ] Agenti specializzati già nel catalog (andrea-marketing, elena-legal, sofia-strategy) — verificare che funzionino per task non-codice
- [ ] Evidence gate per non-codice: il deliverable è un file, non un test. Gate verifica che il file esiste e non è vuoto.
- [ ] Export PDF: un task può produrre un PDF come output (via pandoc o LaTeX)
- [ ] Thor validation per documenti: review qualitativa, non cargo test

### Fase 40b: Integration test COMPLETO — 830 unit + E2E HTTP

**Obiettivo**: Aggiungere veri integration test che avviano il daemon e fanno richieste HTTP.
**Motivazione**: 830 unit test, ZERO test che avviano il server e verificano che le API rispondano.
Learning #13: unit test verdi ≠ sistema funzionante.

#### Task
- [ ] `tests/integration/` directory nel workspace
- [ ] Test fixture: avvia daemon su porta random, aspetta health, esegui test, shutdown
- [ ] Test: create plan → add task → update status → verify gates block invalid transitions
- [ ] Test: create org → add members → query orgchart
- [ ] Test: record token usage → query metrics/cost → verify aggregation
- [ ] Test: SSE stream → create plan → verify event received
- [ ] Aggiungere a CI come job separato (integration-test)

---

## FRONTEND — Convergio Cockpit UI

Repo: https://github.com/Roberdan/convergio-frontend (locale: /Users/Roberdan/GitHub/convergio-frontend)
Stack: Next.js 16, React 19, Maranello design system (100+ componenti Mn*), Tailwind CSS v4
Config-driven: convergio.yaml. Leggere README del repo per dettagli stack.

### Precondizioni frontend
- [x] Daemon convergio operativo (Fase 23 completata, 100+ endpoint)
- [x] `cvg status` funziona
- [ ] `pnpm install && pnpm dev` funziona nel repo frontend (da verificare)

### Checklist chiusura fase frontend
1. pnpm typecheck — zero errori
2. pnpm lint — zero warning
3. pnpm test — test passano
4. pnpm build — build OK
5. Verifica visiva su localhost:3000
6. Worktree isolato, PR, review comments risolti, cleanup post-merge

### Architettura frontend target
```
convergio.yaml                    # config: branding, nav, sezioni
src/app/(dashboard)/
  page.tsx                        # Dashboard live
  orgs/ agents/ plans/ inference/ mesh/ billing/ observatory/ settings/ prompts/
src/lib/
  api.ts  sse.ts  types.ts        # Client HTTP + SSE + tipi
src/hooks/
  use-sse.ts  use-api.ts          # Hook React
```

### Fase 29 (ex Frontend 0): Setup — DONE
- [x] convergio.yaml, api.ts, sse.ts, hooks, types.ts
- Note: PR #7

### Fase 30 (ex Frontend 1): Dashboard live — DONE
- [x] SSE stream, agenti attivi, messaggi real-time, costi, health, delegazioni
- Note: PR #9

### Fase 31 (ex Frontend 2): Organizations — QUASI DONE
- [x] CRUD org, orgchart, delegation view, budget
- [ ] Install org-as-package (needs backend endpoint)
- Note: PR #10

### Fase 32 (ex Frontend 3): Agents — DONE
- [x] Lista live, heartbeat SSE, spawn/kill, delegation chain, runtime view
- Note: PR #11

### Fase 33 (ex Frontend 4): Plans & Tasks — DONE
- [x] Execution tree, task detail, evidence gate, reaper, create plan
- Note: PR #12

### Fase 34 (ex Frontend 5): Inference — DONE
- [x] Model routing, costi trend, budget alerts, fallback chain
- Note: PR #13

### Fase 35 (ex Frontend 6): Mesh — DONE
- [x] Nodi, sync status, schema version, heartbeat timeline
- Note: PR #14

### Fase 36 (ex Frontend 7): Billing — QUASI DONE
- [x] Usage, invoices, rate cards, budget hierarchy
- [ ] Inter-org settlement log (needs backend endpoint)
- Note: PR #15

### Fase 37 (ex Frontend 8): Observability — QUASI DONE
- [x] Timeline, search, dashboard, anomaly detection
- [ ] Export Prometheus/Grafana config
- Note: PR #16

### Fase 38 (ex Frontend 9): Settings — DONE
- [x] Config view, extensions, dependency graph, security/RBAC
- Note: PR #17

### Fase 39 (ex Frontend 10): Prompt Studio — QUASI DONE
- [x] CRUD prompts, skill registry, token usage
- [ ] A/B test results (needs backend endpoint)
- [ ] Spawn preview (needs template resolution)
- Note: PR #18

### Fase 40 (ex Frontend 11): Integration test + polish
- [x] Wiring audit, dead code check, route check, API coverage
- [x] Error states, loading states
- [ ] E2E test Playwright
- [ ] Responsive mobile
- [ ] Theme test (dark/light/navy/colorblind)
- Note: 96 test passano, build OK. E2E deferred.

### Regole UI
- CRUD completo — cockpit, non viewer
- SSE per real-time (MAI polling)
- Nomi UMANI (Elena, Legal Corp) — mai ID
- Solo componenti Maranello (Mn*)
- Errori con dettaglio, filtri su tutto

---

## WORKSPACE SPLIT — STATO 2026-04-04 (aggiornato post-audit)

### Audit codebase — numeri reali (04 Aprile 2026)

| Metrica | Valore |
|---------|--------|
| Crate nel workspace | 26 |
| Extension registrate in main.rs | 18 (tutte con `routes()` → `Some`) |
| Extension NON registrate | depgraph (serve manifests pattern), mcp (binary separato) |
| Test passanti (`cargo test --workspace`) | 830 |
| Righe Rust totali | ~50.000 |
| Endpoint HTTP unici | ~110 (106 crate + 4 server) |
| Tabelle DB (via migrations) | 59+ |
| PR mergiate (#25-#37) | 13 |

### Cosa funziona realmente (verificato con audit codebase)
- **Daemon boot**: main.rs → pool → migrations → 18 extension → routes → serve. Funziona.
- **Auth**: Bearer token + dev-mode localhost bypass. Funziona.
- **Config hot-reload**: watcher con debounce 500ms. Funziona.
- **WAL checkpoint**: graceful shutdown. Funziona.
- **Plan CRUD**: create/list/get/start/complete/cancel/checkpoint. Funziona.
- **IPC**: agents, messages, channels, context, SSE stream. Funziona.
- **Mesh batch sync**: export/import via HTTP con HMAC auth. Funziona (testato localmente).
- **Multi-transport**: Thunderbolt > LAN > Tailscale address resolution. Codice presente, non testato cross-node.
- **Extension routes**: 18/18 registrate ritornano routes. Tutte rispondono a curl.
- **SSE domain events**: DomainEventSink → EventBus → /api/events/stream. plan_created flows.
- **Evidence gates**: record/query/gates/preflight. Funziona.
- **Billing metering**: usage/invoices/rates/alerts. Funziona.
- **Observatory**: timeline/search/dashboard/anomaly. Funziona.

### Cosa NON funziona (CRITICAL GAP)
Il core use case — **delegare lavoro a un altro nodo** — non funziona end-to-end.

| Componente | Stato | Gap |
|-----------|-------|-----|
| **File transport (rsync)** | ASSENTE | Non esiste. Nessun modo di copiare repo + .env a nodo remoto |
| **Remote agent spawning** | ASSENTE | Nessun SSH + `claude` invocazione. agent-runtime traccia agenti ma non li spawna |
| **Real-time DB sync** | ASSENTE | Solo batch export/import via HTTP. Nessun background sync loop |
| **Telegram notifications** | ASSENTE | Solo types in convergio-org (notification_queue). Nessun HTTP client Telegram |
| **Delegation orchestrator** | ASSENTE | Nessun componente che lega file copy → spawn → monitor → sync back |
| **Depgraph in main.rs** | NON WIRED | DepgraphExtension::new() richiede Vec<Manifest> — serve pattern speciale |
| **Agent spawning reale** | ASSENTE | allocator.rs traccia in DB ma non invoca processi. Nessun fork/exec/SSH |
| **Mesh background loop** | ASSENTE | sync_table_with_peer() esiste ma nessun tokio::spawn loop la chiama periodicamente |

**Diagnosi**: 26 crate, 830 test, 110 endpoint — ma il sistema è un **API layer passivo**.
Registra, traccia, serve dati. Non AGISCE. Non spawna agenti, non sincronizza in background,
non copia file, non notifica. DelegateEngine SSH/rsync/tmux del vecchio monolite è stato
escluso dalla migrazione (troppo accoppiato). Nulla lo ha sostituito.

### Backend (daemon) — stato per fase
26 crate, fasi 1-24 complete. PR #25-37 mergiate (13 PRs).
**Fase 23c DONE** (PR #29): 19/19 extension hanno routes reali. Path param fix.
**Fase 24a-24d DONE** (PR #30): Plan protocol — tracking, metadata, gates, aggregation. 825 test.
**Fase 29a DONE** (PR #31): CONSTITUTION.md + README.md.
**Fase 23d PARTIAL**: env, auth, config, WAL, SSE, plan CRUD, IPC, mesh funzionano.
  Mancano: route audit completo, mesh sync 2-nodi, depgraph wiring in main.rs.
**Fase 23d SSE DONE** (PR #32): DomainEventSink trait, EventBus sharing.
**Fase 27b DONE** (PR #33): 8 skill prompts + workflow pipeline seeded.
**Fase 27d DONE** (PR #34): config, schemas, reference docs migrated.
**Fase 27a DONE** (PR #27): .claude/settings.json + 10 script hooks.
**Fase 24e-f DONE** (PR #35): PM endpoints + protocol enforcement.
**Fase 27c DONE** (PR #36): Agent TOML definitions.
**Fase 13b DONE** (PR #37): cvg project init scaffolding.

**Remaining — vecchie fasi non completate**:
- 22: Cutover (manuale, quando Roberto decide)
- 23d remaining: depgraph wiring, mesh sync 2-nodi reale
- 25: Script→daemon (script deprecati ma non rimossi)
- 27f: Script operativi triage (4 deprecati, 4 retained)
- 28: Voice/Telegram completamento

**Remaining — NUOVE FASI (30-35)**: Delegation pipeline end-to-end. Vedi sotto.

### Istruzioni per il prossimo agente
Leggi TUTTO questo file. Il daemon gira come servizio launchd su :8420. Token: `Bearer dev-local`.

**STATO AL 04 APRILE 2026 (sessione 4)**:
- 48 PR mergiate (#25-48) totali
- 833+ test, 19 health checks (depgraph wired), 33+ metriche live
- Agent spawning REALE con monitor + waitpid zombie fix
- Mesh sync loop attivo (macProM1 raggiungibile, auth mismatch HMAC/Bearer)
- Telegram client implementato (manca solo bot token in env)
- launchd plist con PATH completo (claude, gh, git)
- Daemon rebuild automatico dopo ogni PR merge

**CVG CLI**: Nuovo binary installato in ~/.local/bin/cvg (v0.1.0). Build: `cd daemon && cargo build --release -p convergio-cli`.

**PROBLEMI RISOLTI (sessione 4, PR #46+47+48)**:
1. ✅ `claude -p` exit: `--max-turns 50` nel spawner
2. ✅ Zombie reaper: pulisce stage=spawning >1h
3. ✅ DepgraphExtension wired in main.rs (19 componenti, graph validation)
4. ✅ Observatory timeline: sink EventBus → obs_timeline DB
5. ✅ Inference backend: HTTP calls reali Ollama/OpenAI-compatible + echo fallback
6. ✅ Monitor zombie: waitpid(WNOHANG) invece di kill(0)
7. ✅ Spawn esterni: repo_override + instruction_file per repo non-convergio

**FRONTEND (in corso)**:
- Piano daemon ID=5 con 4 wave
- 4 agenti spawnati in convergio-frontend/.worktrees/:
  - jony: committato + PR #24 (orgs CRUD)
  - baccio: committato + PR #25 (responsive + 17 Playwright tests)
  - sara-ux: respawnato (Wave 1: data layer)
  - nasra: respawnato (Wave 3: real-time)

**PROSSIMI PASSI (in ordine — NON saltare)**:
1. **CRITICO — Fase 32b**: Agent→Plan lifecycle wiring. Il monitor DEVE aggiornare task e piano. Senza questo il sistema sembra morto.
2. **CRITICO — Fase 32c**: Planner E2E. Ogni piano deve essere completo e validabile PRIMA dell'esecuzione.
3. **CRITICO — Fase 32d**: Thor a livello piano. Pre-review (challenger) + post-review (validazione finale).
4. Merge PR frontend + monitorare agenti frontend
5. Mesh sync: risolvere auth mismatch
6. Fase 34: delegation orchestrator
Vecchio repo reference: `/Users/Roberdan/GitHub/ConvergioPlatform`.
**GAP CRITICO**: Il daemon è un API layer passivo — non spawna agenti, non sincronizza in background,
non copia file tra nodi. Le fasi 30-35 colmano questo gap.
**Fase 32 DONE** (PR #38+40+41+42+45): Agent spawning reale con monitor chiuso:
  spawn → agent works → commit → monitor detects exit → push → PR automatica.
  Fix: branch, log files, claude abs path, no timeout wrapper, spawn monitor, plist PATH.
  Fix: branch (non detached), log files (non /dev/null), claude abs path, no timeout wrapper.
  Testato: agente spawnato da daemon launchd → ha committato autonomamente.
**Fase 38c PARTIAL**: launchd plist + install-service.sh + add-mesh-node.sh creati dall'agente marco-devops (cherry-picked in PR #40). Firewall non gestibile su Mac managed.
**Health/Metrics WIRED** (PR #40): /api/health/deep mostra 18 componenti, /api/metrics mostra 33 metriche.
**Priorità**: Fase 38c (daemon auto-start) → 30 (DB sync) → 31 (file transport) → 33 (Telegram) → 34 (orchestrator) → 35 (E2E test).

### Frontend (cockpit UI)
Fasi 29-38 DONE. Fasi 31/36/37/39 quasi done (mancano endpoint backend). Fase 40 parziale (E2E, responsive).

### Ordine esecuzione rimanente
```
STEP 0: IL LOOP DEVE CHIUDERSI (senza questo tutto il resto è inutile)
  → 32b (agent→task→plan lifecycle wiring — IL FIX PIÙ CRITICO)
  → 32c (planner E2E — piani completi e validabili)
  → 32d (Thor piano-level — challenger pre + validatore post)

STEP 1: FONDAMENTA
  → 23e (depgraph wiring)
  → 38c fix (plist PATH già OK, verificare firewall)

STEP 2: DELEGATION PIPELINE
  → 30 ✅ (mesh sync loop — DONE PR #43)
  → 31 (file transport — rsync)
  → 37b (node capability registry)
  → 33 ✅ (Telegram — DONE PR #44, manca bot token)
  → 34 (delegation orchestrator — compone tutto)
  → 35 (E2E test)

STEP 3: COMPLETAMENTO
  → 36b (inference reale — Ollama/API)
  → 39b (progetti non-codice)
  → 40b (integration test HTTP)
  → Frontend rebuild

STEP 4: SELF-HOSTING
  → 26 (convergio costruisce convergio)
```

**REGOLA D'ORO**: Non passare allo step successivo finché lo step corrente
non è VERIFICATO end-to-end con Roberto che VEDE il risultato nella UI.
Step 0 non è "fatto" finché Roberto non vede i piani aggiornarsi automaticamente.
```

### Cosa serve per usare convergio per finire convergio (Fase 26 bootstrap)

Oggi convergio NON può finire se stesso perché manca lo spawning reale (Fase 32).
Il path minimo per il self-hosting è:
1. **38c**: daemon auto-start (così gira sempre)
2. **32 (solo spawn locale)**: spawn un agente Claude su QUESTO nodo in un worktree
3. Il daemon crea il piano "Completa Fase 30" → spawna un agente → l'agente lavora → committa → PR
4. Per questo NON servono mesh sync, file transport, o Telegram — solo spawn locale

Quindi: **Fase 32 (spawn locale only)** è il MINIMO per il self-hosting. Tutto il resto (mesh, transport, Telegram) è per il multi-nodo.

## CONSTITUTION

Questo file è la specifica di riferimento per l'intero progetto.
Ogni agente lo legge PRIMA di fare qualsiasi cosa.
Le regole sono non-negoziabili.

### Regola 1: Mai la via breve — sempre la causa radice
NEVER take the quick path. ALWAYS fix the root cause.
- Non aggiungere workaround — fixa il codice rotto.
- Non skippare test — fixa il codice che fallisce.
- Non copiare pattern senza capirli — capisci perché funzionano.
- 3 fix consecutivi che introducono nuovi problemi → STOP, ricostruisci.
- I workaround diventano permanenti. Le scorciatoie diventano debito.

### Regola 2: Integration test obbligatorio
Unit test verdi NON sono evidence di "funziona".
Ogni fase si chiude con smoke test end-to-end contro il sistema running.
Learning #13-14: 793 unit test verdi, daemon che non funziona.

### Regola 3: Isolamento workspace
Ogni task in worktree separato sotto `.worktrees/`. Mai sul checkout principale.
Un worktree = un branch = una PR. Cleanup obbligatorio post-merge.

### Regola 4: Regole prima degli agenti
Le regole devono esistere PRIMA di lanciare gli agenti. Mai aggiungere regole a sessioni in corso.

### Regola 5: Evidence verificabile
Mai accettare "done" senza proof. Commit hash, curl output, test output, screenshot.
Thor valida. L'evidence gate rifiuta self-reported senza verifica.

### Regola 6: Il planner prevede tutto
Ogni piano include: integration test per wave, wiring verification, smoke test finale.
Mai pianificare "crea crate" senza "verifica che il daemon li serva".
L'orchestratore automatico produce scaffolding se il planner non chiede integration.

### Regola 7: Prima esplorare quello che esiste, poi costruire
MAI costruire un componente, una funzione, un modulo senza PRIMA verificare cosa esiste già.
- Frontend: PRIMA leggi i componenti Maranello disponibili (src/components/maranello/), poi scegli quello giusto per il caso d'uso. Non prendere un componente a caso — cerca quello fatto per quel tipo di dato.
- Backend: PRIMA leggi i crate esistenti e le loro API, poi decidi se serve codice nuovo.
- Design system: PRIMA esplora le categorie (agentic/, data-viz/, data-display/, forms/, etc.), capisce cosa ogni componente fa, poi usa quello appropriato.
- Vecchio repo: PRIMA cerca se il vecchio ConvergioPlatform aveva già risolto il problema, poi adatta.
Chi costruisce senza esplorare produce duplicati, usa componenti sbagliati, e ignora lavoro già fatto.
Questo vale per OGNI decisione: librerie, pattern, architettura, UI. Esplorare → capire → decidere → costruire.

### Regola 8: Mai bypassare niente senza approvazione esplicita dell'utente
Nessun hook, regola, check, gate, o vincolo può essere disabilitato, skippato, o aggirato senza approvazione esplicita dell'utente (Roberdan). Questo include:
- Hook che bloccano (FileSizeGuard, MainGuard, ThorGateGuard) — non si disabilitano
- Test che falliscono — non si cancellano o si skippano
- CI che non passa — non si forza il merge
- Evidence gate — non si dichiara "done" senza proof
- Branch protection — non si committa su main
- Qualsiasi regola di questa constitution
Se un vincolo blocca il lavoro, FERMATI e chiedi all'utente. Non decidere da solo di bypassare.

### Regola 9: Conserva il contesto — non rileggere, non sprecare token
Il contesto è una risorsa finita. Ogni token sprecato accorcia la vita dell'agente.
- Non rileggere file già letti nella stessa sessione — referenzia le letture precedenti.
- Usa offset/limit per file grandi — non leggere 1200 righe se te ne servono 10.
- Se hai già letto WORKSPACE-SPLIT.md, non rileggerlo intero — leggi solo la sezione che serve.
- Delega task meccanici a Copilot per risparmiare il tuo contesto per decisioni architetturali.
- Quando il contesto raggiunge il 70-80%, salva checkpoint e prepara il handoff al prossimo agente.

### Regola 10: Ogni feature DEVE chiudere il loop end-to-end
NON dichiarare una feature "fatta" se il loop non è chiuso. Il loop è:
```
input → elaborazione → output → feedback → stato aggiornato → visibile all'utente
```
Se manca anche UN SOLO pezzo, la feature NON funziona. Esempi concreti:
- Agent spawning SENZA update del piano = sistema sembra morto (Learning #19)
- Routes SENZA wiring in main.rs = endpoint 404 (Learning #14)
- Health check SENZA registrazione nel registry = dashboard vuoto (Learning #18)
- Domain events SENZA persistence in DB = timeline vuota (Learning #24)
- Inference router SENZA backend reale = echo inutile (Learning #15)

**Test del loop**: prima di dichiarare done, fai l'intero percorso dall'inizio alla fine
e verifica che l'UTENTE FINALE veda il risultato. Se l'utente non lo vede, non è fatto.

### Regola 11: Il workflow è un contratto, non un suggerimento
Il workflow solve→planner→execute→thor DEVE essere enforced dal sistema, non dalla
buona volontà dell'agente. Ogni transizione di stato deve essere:
1. **Validata** da un gate (ImportGate, StartGate, TestGate, EvidenceGate, ValidatorGate)
2. **Registrata** nel DB con timestamp
3. **Emessa** come DomainEvent (per SSE → UI e persistence → timeline)
4. **Verificabile** post-facto nell'audit trail

Se un agente può bypassare una transizione, il workflow è rotto.

### Regola 12: Auto-organizzazione = osservabilità + feedback loop
Il sistema deve auto-adattarsi solo se ha DATI su cui basarsi. Senza metriche, senza
feedback, senza monitoraggio → il sistema non può auto-organizzarsi, può solo ripetere errori.

Requisiti per l'auto-organizzazione:
1. **Ogni azione ha un costo tracciato** — token, tempo, compute. Se non sai quanto costa, non puoi ottimizzare.
2. **Ogni risultato ha una qualità misurata** — Thor valida, evidence gate verifica, test passano.
3. **Ogni errore produce un learning** — non basta fixare, bisogna documentare PERCHÉ è successo.
4. **I pattern negativi sono rilevati automaticamente** — cascading fix threshold (Regola 1),
   3 agenti che falliscono sullo stesso task → il sistema si ferma e chiede all'utente.
5. **I pattern positivi sono amplificati** — se un agente produce buon codice con Haiku (economico),
   il router ricorda e usa Haiku per task simili in futuro.

### WORKFLOW COMPLETO — come DEVE funzionare (contratto)

```
1. PROBLEMA ARRIVA (utente o sistema)
   → /solve o POST /api/plan-db/create con objective+motivation
   → Piano creato con status=draft

2. PIANIFICAZIONE
   → /planner O agente PM analizza e scompone in wave/task
   → Ogni task ha: titolo, agente assegnato, tier, budget, wave
   → Piano status: draft → todo → approved (dopo review)

3. ESECUZIONE (per ogni wave, in ordine)
   → Per ogni task nella wave:
     a. POST /api/agents/spawn con task_id, agent_name, instructions, tier
     b. Daemon crea worktree + lancia processo
     c. Monitor si aggancia al PID
     d. Agente lavora → committa
     e. Monitor rileva exit → push → PR
     f. Monitor aggiorna task status → submitted [FASE 32b — MANCA]
     g. Monitor emette TaskCompleted event [FASE 32b — MANCA]
   → Quando tutti i task della wave sono submitted → wave_done
   → Orchestrator emette wave_needs_validation

4. VALIDAZIONE (Thor)
   → Thor riceve wave_needs_validation
   → Per ogni task: verifica evidence (commit, test, PR)
   → Se passa → task status: done
   → Se non passa → task status: failed, feedback all'agente
   → Wave validata → prossima wave O piano done

5. COMPLETAMENTO
   → Tutti i task done → piano status: done
   → PM compila report (costi, durate, learnings)
   → Notifica (SSE + Telegram)
   → Cleanup: worktree rimossi, branch puliti

6. LEARNING
   → PM aggrega learnings da tutti i task
   → Se pattern negativo ricorrente → nuova regola nel CLAUDE.md
   → Se pattern positivo → modello routing aggiornato
```

### BUCHI ATTUALI NEL WORKFLOW (da fixare)

| Step | Stato | Cosa manca | Fase |
|------|-------|-----------|------|
| 1. Problema→Piano | ✅ API | — | — |
| 2. Piano→Wave/Task | ✅ API | Planner automatico (oggi manuale) | — |
| 3a. Spawn agente | ✅ | — | 32 |
| 3b. Worktree+processo | ✅ | — | 32 |
| 3c. Monitor | ✅ | — | 45 |
| 3d. Commit | ✅ | — | — |
| 3e. Push+PR | ✅ | — | 45 |
| **3f. Task→submitted** | ❌ | Monitor non aggiorna task | **32b** |
| **3g. TaskCompleted event** | ❌ | Monitor non emette evento | **32b** |
| **Wave auto-progression** | ❌ | Nessuno conta task e avanza wave | **32b** |
| **4. Thor validation** | ❌ | Reactor ascolta ma nessuno invoca | **32b** |
| **5. Plan→done** | ❌ | Resta todo per sempre | **32b** |
| **5. Report PM** | ❌ | PM endpoints esistono, nessuno li chiama | **32b** |
| **5. Notifica** | ❌ | Telegram client esiste, nessuno lo chiama | **32b** |
| **5. Cleanup** | ❌ | Worktree restano, branch non puliti | future |
| **6. Learning** | ❌ | Manuale, non automatico | future |

**Fase 32b è il FIX per i buchi 3f→5. È la priorità assoluta.**

### Come viene letta la constitution
- **CLAUDE.md** nei repo (backend + frontend): caricato automaticamente ad ogni sessione Claude.
  Contiene le regole critiche in forma compatta.
- **WORKSPACE-SPLIT.md** (questo file): reference completo con learnings, contesto, ragionamento.
  I CLAUDE.md puntano qui per le decisioni non-triviali.

Quando convergio sarà operativo, le regole qui scritte diventano codice:
- Regola 1 → cascading fix threshold nel planner
- Regola 2 → evidence gate con curl test obbligatorio
- Regola 10 → integration test E2E che verifica il loop completo
- Regola 11 → lifecycle gates enforced nel codice, non nei commenti
- Regola 12 → metriche + feedback loop automatico
- Regola 3 → agent runtime workspace isolation
- Regola 4 → prompt injection at spawn
- Regola 5 → Thor validation gate
- Regola 6 → planner con integration test mandate

**Un unico file. Una unica source of truth.**
Ogni agente lo legge PRIMA di fare qualsiasi cosa. Le regole sono non-negoziabili.

---

## Learnings sessione 4 (04 aprile 2026)

12. **kill(pid, 0) non rileva zombie processes**: il monitor usava `libc::kill(pid, 0)` che restituisce 0 per processi zombie. Risultato: monitor non rileva mai la morte dell'agente. **Fix**: `waitpid(pid, WNOHANG)` raccoglie il zombie E restituisce l'exit code. (Learning #21)

13. **nohup + cd chain = tutti gli agenti nella stessa directory**: spawno 4 agenti con `cd dir1 && nohup claude &; cd dir2 && nohup claude &` — tutti finiscono nell'ultimo `cd`. **Root cause**: i `cd` nella stessa shell si accumulano. **Fix**: ogni agente in subshell isolata: `(cd dir && nohup claude </dev/null &)`. Il vecchio ConvergioPlatform usava tmux (`tmux new-window -d -c $dir`) che gestisce CWD per finestra. (Learning #22)

14. **Il daemon spawner deve supportare repo esterni**: lo spawner assume `repo_root = convergio` e crea worktree lì. Per il frontend serve `repo_override` nel body. Anche `instruction_file` serve per leggere file pre-esistenti (AGENT-*.md) invece di scrivere TASK.md. (Learning #23)

15. **EventBus → SSE ma non → DB**: domain events finivano solo in SSE (broadcast channel). Se nessun client SSE è connesso, gli eventi si perdono. **Fix**: observatory sink sottoscrive al bus e persiste in obs_timeline. (Learning #24)

16. **META-LEARNING: Il sistema costruisce pezzi ma non li collega (pattern ricorrente)**.
    Ogni sessione scopre che un pezzo "funziona" in isolamento ma non è collegato al resto:
    - Sessione 2: crate compilano ma routes()→None (Learning #14)
    - Sessione 3: health/metrics implementati ma non registrati in main.rs (Learning #18)
    - Sessione 3: agenti lavorano ma piani non si aggiornano (Learning #19)
    - Sessione 4: inference router decide ma non chiama modelli reali (Learning #15)
    - Sessione 4: observatory timeline vuota perché sink non persisteva (Learning #24)
    **Root cause**: la pianificazione è bottom-up (crea il pezzo, poi pensa al wiring).
    Dovrebbe essere top-down (definisci il loop E2E, poi implementa ogni pezzo GIÀ WIRED).
    **Regola per il futuro (Regola 10)**: ogni feature si pianifica come loop chiuso.
    Il PRIMO task è definire input→output→feedback→stato→visibilità.
    L'ULTIMO task è verificare che l'utente veda il risultato.
    **Come evitare**: prima di ogni fase, l'agente DEVE rispondere a:
    1. Chi produce l'input?
    2. Chi consuma l'output?
    3. Come l'utente lo vede?
    4. Come il sistema registra che è stato fatto?
    Se non sai rispondere a tutte e 4 → la fase non è pronta per essere eseguita.

---

## Fase 27a — Guardrails migration (2026-04-04)

**Obiettivo**: Portare tutti i guardrail da ConvergioPlatform a convergio. Non copy-paste: analisi, ottimizzazione, eliminazione di ciò che non serve nel nuovo repo.

**Stato**: ✅ Completata

### Cosa è stato portato (ottimizzato)

| # | Guard | Tipo | File convergio | Note |
|---|---|---|---|---|
| G1 | MainGuard (git) | pre-commit | `scripts/hooks/git-pre-commit.sh` | Block commit su main |
| G2 | FileSizeGuard (git) | pre-commit | `scripts/hooks/git-pre-commit.sh` | Max 250 lines .rs/.ts/.js/.sh |
| G3 | SecretScan (git) | pre-commit | `scripts/hooks/git-pre-commit.sh` | API keys, tokens, passwords |
| G4 | SqliteBlock (git) | pre-commit | `scripts/hooks/git-pre-commit.sh` | No sqlite3 in .sh/.py |
| G5 | CommitLint (git) | commit-msg | `scripts/hooks/git-commit-msg.sh` | Conventional commits |
| C1 | SecretScan (Claude) | PreToolUse/Bash | in pre-tool-guard.sh | — |
| C2 | SqliteBlock (Claude) | PreToolUse/Bash | in pre-tool-guard.sh | — |
| C4 | Clippy on .rs edits | PostToolUse/Edit | inline + worktree CARGO_TARGET_DIR | Upgrade: per-crate + workspace fallback |
| C5 | EvidenceGate | SubagentStop | `subagent-completion-gate.sh` | WARNING, non block |
| C6 | FileSizeGuard (Claude) | PostToolUse/Edit+Write | inline settings.json | Max 250 lines |
| C7 | RustModWiring | PostToolUse/Edit+Write | `check-rust-wiring.sh` | + router merge + dead module check |
| C8 | FailLoud | PreToolUse/Edit | in pre-tool-guard.sh | unwrap_or_default, let _ = |
| C9 | MainGuard (Claude) | PreToolUse/Edit+Write | `main-guard.sh` | Block writes su main |
| C10 | MainDirtyCheck | SubagentStart | `main-dirty-check.sh` | WARNING >5 dirty files |
| — | BlockBranchCreation | PreToolUse/Bash | `block-branch-creation.sh` | Enforce worktree discipline |
| — | ThorGateGuard | PreToolUse/Bash | `thor-gate-guard.sh` | Only Thor sets done |
| — | CommitLint (Claude) | PreToolUse/Bash | in pre-tool-guard.sh | Conventional commit check |
| — | EvidenceGate (commit) | PreToolUse/Bash | in pre-tool-guard.sh | Test marker <10min |
| — | PreCompact | PreCompact | `pre-compaction-snapshot.sh` | cvg checkpoint save-auto |
| — | IPC Notification | Notification | inline settings.json | Inbox check per agent |
| — | Preflight checks | SubagentStart | inline settings.json | gh auth, cvg, daemon, identity |

### Cosa NON è stato portato (con motivazione)

| Vecchio guard | Perché escluso |
|---|---|
| `ipc-message-inject.sh` su ogni PreToolUse | Troppo costoso. Spostato solo in Notification |
| `plan-db.sh` guards | Non esiste in convergio. cvg CLI copre il caso |
| `npm run` blocks | Repo Rust-only, niente JS |
| `gh run view --log` / `gh pr checks` blocks | Troppo restrittivo per nuovo repo |
| `EnterPlanMode` block | Eccessivo — /planner skill è suggerito, non forzato |
| `settings.json` edit protection | Non necessario, diversa struttura progetto |
| `plan spec files` protection | Non esiste in convergio |
| `agent-bridge.sh` SubagentStart register | Troppo accoppiato al daemon. Graceful via env check |
| `subagent-auto-submit.sh` | Troppo accoppiato al daemon IPC. completion-gate copre la safety |

### Ottimizzazioni rispetto a ConvergioPlatform

1. **Consolidamento pre-tool-guard**: da 181 linee a 86 — rimossi 8 guard ConvergioPlatform-specific
2. **Clippy migliorato**: worktree isolation con `CARGO_TARGET_DIR` separato per non lockare il target/ del daemon
3. **MainGuard esteso**: ora guarda `daemon/`, `scripts/`, `.claude/` (non solo `daemon/src/`)
4. **Git hooks installabili**: symlink pattern `ln -sf ../../scripts/hooks/git-*.sh .git/hooks/`
5. **Permissions granulari**: 23 allow + 9 deny (vs vecchio: 29 allow, 9 deny — rimossi npm/python3)
6. **6 hook events coperti**: PreToolUse, PostToolUse, SubagentStart, SubagentStop, PreCompact, Notification

### File creati
```
.claude/settings.json           — permissions + 6 hook events
scripts/hooks/main-guard.sh     — C9 MainGuard
scripts/hooks/block-branch-creation.sh — BlockBranchCreation
scripts/hooks/thor-gate-guard.sh — ThorGateGuard
scripts/hooks/main-dirty-check.sh — C10 MainDirtyCheck
scripts/hooks/pre-tool-guard.sh  — C1+C2+C8+CommitLint+EvidenceGate
scripts/hooks/check-rust-wiring.sh — C7 RustModWiring
scripts/hooks/subagent-completion-gate.sh — C5 EvidenceGate+auto-commit
scripts/hooks/pre-compaction-snapshot.sh — PreCompact
scripts/hooks/git-pre-commit.sh  — G1+G2+G3+G4
scripts/hooks/git-commit-msg.sh  — G5 CommitLint
```

---

## Lezioni per il workflow

> Qui annotiamo cosa il workflow automatico AVREBBE DOVUTO catturare.
> Alla fine, queste diventano le regole del workflow blindato.

1. 10056: 38 task submitted senza verifica → il workflow deve matchare commit a task
2. 10056: 4 task fraudolenti (status avanzato, lavoro non fatto) → evidence deve essere verificabile, non just "posted"
3. 10056: Thor mai invocato → wave completion deve triggerare Thor automaticamente
4. **WORKSPACE-SPLIT sessione 1**: agenti paralleli senza worktree isolati creano casino:
   - Fase 8 (Copilot) ha creato branch `feat/convergio-cli` nel checkout principale, inquinando lo spazio condiviso
   - Fase 7 (Claude) ha switchato il checkout su `feat/orchestrator-crate`, spostando tutti sotto un branch non suo
   - Commit mesh (fase 6) è finito sul branch sbagliato, servito cherry-pick manuale per riportarlo su main
   - Fase 8 ha committato CLI e orchestrator sullo stesso branch — lavoro di 2 fasi mischiato
   - **Root cause**: nessun isolamento filesystem. Tutti lavoravano sullo stesso checkout.
   - **Fix**: worktree obbligatori (regola aggiunta sopra). Un worktree = una fase = un branch = una PR.
5. **WORKSPACE-SPLIT sessione 1**: agenti non leggono le regole aggiunte a sessione in corso.
   - Le regole di isolamento sono state aggiunte al tracker DOPO che le sessioni 7 e 8 erano già partite.
   - **Fix**: le regole devono essere nel tracker PRIMA di lanciare gli agenti. Mai aggiungere regole operative a sessioni già attive — non le vedranno.
6. **WORKSPACE-SPLIT sessione 1**: agenti non fanno la checklist di chiusura se non la conoscono dall'inizio.
   - Fase 6 completata senza commit. Fase 8 completata con commit su branch sbagliato. Nessuna PR.
   - **Fix**: la checklist di chiusura fase è ora nel tracker. Verificare che sia presente PRIMA di lanciare wave.

7. **WORKSPACE-SPLIT sessione 1**: `claude -p` con prompt lungo (>3000 chars) come argomento causa hang silenzioso.
   - Il prompt dell'orchestratore (~3500 chars) passato come `claude -p "$(cat file.md)"` non produceva output.
   - Prompt corti (~200 chars) funzionano perfettamente con tool use.
   - **Root cause**: prompt troppo lungo come argomento shell, probabilmente troncato o mal-escapato.
   - **Fix**: prompt corto che dice a Claude di LEGGERE il file con le istruzioni complete. Pattern:
     `claude -p "Leggi scripts/orchestrator-prompt.md per le istruzioni, poi inizia"` — Claude legge il file con Read tool.
   - **Regola per convergio Fase 17**: quando il daemon spawna un agente, il prompt di spawn deve essere corto. Le istruzioni dettagliate vanno in un file che l'agente legge al primo turno.
8. **WORKSPACE-SPLIT sessione 1**: `</dev/null` con `claude -p` causa errore "Input must be provided through stdin or as prompt argument".
   - `-p` è sia flag che argomento. Con `</dev/null` stdin viene chiuso e Claude non trova il prompt.
   - **Fix**: non usare `</dev/null` con `-p`. Il prompt è nell'argomento, stdin non serve.
9. **WORKSPACE-SPLIT sessione 1**: heredoc bash con backtick e single quote dentro causa "unexpected EOF".
   - Lo script orchestrator.sh usava `cat <<'PROMPT_EOF'` ma il contenuto aveva backtick che confondevano bash.
   - **Fix**: prompt in file separato (.md), lo script lo legge con `cat`.
   - **Regola per convergio**: i prompt degli agenti vanno SEMPRE in file separati, mai inline in shell script.
10. **WORKSPACE-SPLIT sessione 1**: pattern testato e funzionante per lanciare Claude non-interattivo:
    ```bash
    timeout 7200 claude --dangerously-skip-permissions \
        --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent" \
        --add-dir "$REPO" \
        --model claude-opus-4-6 \
        -p "Prompt corto. Leggi <file> per istruzioni complete."
    ```
    - `--allowedTools` esplicito per evitare prompt di permessi
    - `--add-dir` per dare accesso al repo
    - `timeout` per evitare hang infiniti
    - Prompt corto + file di istruzioni letto con Read tool
    - Auto-restart con `exec "$0"` quando il contesto si esaurisce
11. **WORKSPACE-SPLIT sessione 1**: l'orchestratore non pulisce worktree e branch dopo il merge delle PR.
    - Dopo merge di fasi 9-13, i worktree restavano in `.worktrees/` e i branch locali non venivano cancellati.
    - 6 branch stale + 2 worktree orfani trovati dopo ispezione manuale.
    - **Root cause**: il prompt dell'orchestratore dice "crea worktree, crea PR, mergia PR" ma non dice "dopo merge rimuovi worktree e branch".
    - **Fix**: aggiunto al prompt orchestratore e alla checklist. Dopo ogni merge:
      1. `git worktree remove .worktrees/fase-N --force`
      2. `git branch -D feat/fase-N-crate`
      3. `git remote prune origin`
    - **Regola per convergio Fase 17**: il reaper del runtime deve pulire workspace isolati dopo task completato. Nessun residuo orfano.
12. **WORKSPACE-SPLIT sessione 1**: l'orchestratore autonomo funziona — ha completato 6 fasi (9→14) da solo.
    - Pattern: prompt corto → legge istruzioni da file → controlla stato → lancia fasi → crea PR → aspetta CI → mergia → next.
    - Gestisce errori API transitori (500) con retry automatico (context crunch + ripresa).
    - Non richiede intervento umano per il ciclo base.
    - **Limiti osservati**: non pulisce worktree (fix sopra), non gestisce conflitti merge complessi, si ferma su errori non-transitori.
    - **Regola per convergio**: questo pattern (orchestratore che spawna worker, monitora, mergia, pulisce) è il prototipo della Fase 17 (agent runtime). Il daemon deve fare esattamente questo ma con enforcement, isolation, e cleanup automatico.
13. **WORKSPACE-SPLIT sessione 1**: ERRORE GRAVE DI PIANIFICAZIONE — costruire crate isolati senza integration testing.
    - 20 fasi hanno creato 26 crate con 793 unit test. Tutto compila, tutto verde.
    - Ma il daemon non funzionava: auth rotta (token non caricato), route delle extension non registrate, cvg CLI incompatibile, env file non letto, path sbagliati.
    - **Root cause**: ogni fase testava il suo crate in isolamento. Nessuna fase verificava che il sistema funzionasse end-to-end. Il wiring (Fase 21) era uno stub. L'integration test era assente.
    - **Il piano trattava la migrazione come "sposta codice" invece di "costruisci sistema funzionante".**
    - **Fix**: aggiunta Fase 23 (integration hardening). Ma il fix vero è nella pianificazione:
      1. Ogni wave DEVE chiudersi con un integration test: il daemon parte, risponde a curl, le API funzionano
      2. Mai dichiarare "done" basandosi solo su unit test — serve smoke test end-to-end
      3. Il wiring non è una fase separata — è parte di OGNI fase. Quando crei un crate con routes(), verifica che il daemon le serva
      4. L'auth non è un dettaglio — è la prima cosa che rompe tutto. Testarla subito, non alla fine.
    - **Regola per convergio Fase 20**: l'evidence gate DEVE includere integration test. Unit test verdi NON sono evidence sufficiente di "funziona".
14. **WORKSPACE-SPLIT sessione 2**: L'ORCHESTRATORE AUTOMATICO PRODUCE CRATE VUOTI.
    - Audit 2026-04-04: su 19 extension, solo 9 ritornano `Some` da `routes()`. Le altre 10 ritornano `None`.
    - 7 crate hanno logica interna reale (prompts, evidence, backup, longrunning, mesh, ipc, voice) ma NON la espongono via HTTP — il daemon non sa che esistono.
    - 3 crate (org, org-package, kernel) sono puro scaffolding: migrations SQL + `health() → Ok` + zero handler. Compilano, testano verde, non fanno nulla.
    - **Root cause**: l'orchestratore automatico ha ottimizzato per "compila + test verde", non per "funziona nel sistema". Ha creato struct, impl, test — ma mai collegato al daemon.
    - **Il planner DEVE includere per ogni fase**:
      1. `routes()` ritorna `Some(router)` con endpoint reali
      2. `curl` al daemon per verificare che gli endpoint rispondono
      3. Almeno un integration test che chiama l'API dal CLI o da HTTP
      4. MAI dichiarare done basandosi solo su `cargo test` — serve evidenza end-to-end
    - **Impatto**: 10 crate, ~300 test, ~4000 righe di codice che non contribuiscono nulla al daemon funzionante. Tutto da rifare.
15. **WORKSPACE-SPLIT sessione 3 (audit 04 Aprile 2026)**: Bottom-up building without integration produces components that don't compose.
    - 26 crate, 830 test, 110 endpoint — ma il core use case (delegare lavoro a un altro nodo) non funziona end-to-end.
    - Ogni crate funziona in isolamento. La COMPOSIZIONE è ciò che manca.
    - Il mesh ha export/import HTTP ma nessun background sync loop. L'agent-runtime traccia agenti in DB ma non ne spawna nessuno (nessun fork/exec/SSH). Le notification hanno la coda ma nessun HTTP client Telegram.
    - Il vecchio DelegateEngine (SSH + rsync + tmux) è stato escluso dalla migrazione perché troppo accoppiato. Nulla lo ha sostituito.
    - **Root cause**: il piano di migrazione trattava ogni crate come unità indipendente. Nessuna fase ha mai testato "il sistema delega un task a un altro nodo end-to-end".
    - **Fix**: Fasi 30-35 progettate specificamente per il pipeline di delegation end-to-end.
    - **Regola**: ogni feature che coinvolge 2+ crate DEVE avere un integration test cross-crate prima di dichiarare done.
16. **WORKSPACE-SPLIT sessione 3**: Agents delegated to subagents should run `cargo fmt` before committing.
    - CI caught fmt failures on agent-produced code (PR #37).
    - **Fix**: aggiungere `cargo fmt` alla checklist pre-commit degli agenti. I pre-commit hook dovrebbero bloccare codice non formattato.
17. **WORKSPACE-SPLIT sessione 3**: La delegation NON deve essere accoppiata a un singolo modello/tool.
    (vedi learning #17 sopra per dettagli)
18. **WORKSPACE-SPLIT sessione 3 — PRIMO AGENT SPAWN REALE (04 Aprile 2026)**:
    Il daemon ha spawnato `marco-devops` (Sonnet t2) per Fase 38c. L'agente HA FUNZIONATO — ha creato 3 file (plist, install-service.sh, add-mesh-node.sh) e committato.
    Ma ha rivelato 7 problemi critici del runtime:
    - **Zombie process**: stdout/stderr → /dev/null. Nessun log visibile. Fix: log a file nel worktree.
    - **No push/PR**: worktree è detached HEAD, l'agente non può pushare. Fix: creare branch prima dello spawn.
    - **Health/deep vuoto**: extensions implementano HealthCheck ma main.rs NON le registra nel HealthRegistry.
    - **Metrics vuoto**: extensions implementano MetricSource ma main.rs NON le registra nel MetricsCollector.
    - **Observatory vuoto**: DomainEventSink→SSE ma NON scrive nella timeline. Il dashboard è vuoto.
    - **Token tracking assente**: l'agente lavora ma nessun costo viene registrato automaticamente.
    - **Error rate 51%**: /api/plan-db/list ha 16/17 errors (vecchio CLI con parametri sbagliati).
    - **Root cause**: il wiring in main.rs non completa il loop — crea HealthRegistry e MetricsCollector ma non registra le extension. Ogni extension ha il codice per farlo, nessuno lo chiama.
    - **Impatto**: la UI mostra dashboard vuoti, nessun health check, nessuna metrica. Il sistema SEMBRA morto anche quando funziona.

## Piano 10056
    - Roberto: "non sempre Claude, dobbiamo ottimizzare i token".
    - `convergio-inference` ha GIÀ il model router (Fase 11): classifica il task → sceglie tier → downgrade se budget basso.
    - Ma la Fase 32 (spawning) era progettata solo per `claude -p`. Deve supportare: Claude CLI, gh Copilot, API diretta (Anthropic/OpenAI/Ollama), script deterministici.
    - L'utente deve poter scegliere: `--model claude-opus-4-6` (override) O lasciare che il router decida (default).
    - **Root cause**: le fasi erano pensate in isolamento. Il router (Fase 11) e lo spawner (Fase 32) non erano connessi nel design originale.
    - **Fix**: Fase 32 aggiornata. Lo spawner chiama il router prima di decidere il backend. Task semplici → Haiku/local, task complessi → Opus. Budget-aware.

19. **WORKSPACE-SPLIT sessione 3 — AGENTI NON AGGIORNANO I PIANI (04 Aprile 2026)**:
    - Roberto vede tutti i piani "queued" nella UI anche dopo che il lavoro è stato fatto e mergiato.
    - Il piano #3 (launchd) ha i file creati, committati, mergiati — ma lo status è ancora `todo`.
    - **Root cause**: il loop non è chiuso. Lo spawn_monitor aggiorna l'agente (stage→stopped)
      e fa push+PR, ma NON aggiorna il task nel piano e NON avanza lo stato del piano.
    - Il reactor dell'orchestratore ascolta su IPC per eventi `task_done` → `wave_done` → `plan_done`,
      ma nessuno emette `task_done` quando l'agente finisce.
    - **Impatto**: il sistema SEMBRA non funzionare. La UI mostra tutto fermo. Roberto pensa che
      niente stia succedendo. Il lavoro viene fatto ma non è visibile.
    - **Fix**: Fase 32b — wiring monitor→task→plan. Il monitor deve chiudere il loop completo.
    - **Regola**: ogni pezzo che produce un risultato DEVE aggiornare lo stato nel DB E emettere
      un evento domain. Se il DB non riflette la realtà, il sistema è rotto.

## Piano 10056 — Task assorbiti

| Task 10056 | Assorbito in | Note |
|------------|-------------|------|
| F-41 Remove CRSQLite | Fase 0 pulizia | |
| F-42 Remove __disabled feature | Fase 0 pulizia | |
| F-17 Unwrap elimination | Ogni fase | Man mano che tocchiamo i file |
| F-49 Circuit breaker mesh | Fase 6 mesh | |
| F-50 HMAC replay protection | Fase 6 mesh | |
| F-51 In-memory IPC fast path | Fase 5 ipc | |
| F-20 Rate limiter | Fase 5 ipc | |
| F-21 IPC connection limit | Fase 5 ipc | |
| F-44 Delta sync | Fase 6 mesh | |
| F-47 Parallel peer sync | Fase 6 mesh | |
| F-60 Prometheus metrics | Fase 2 telemetry | |
| F-34 Remove email stub | Fase 0 pulizia | Era fraudolentemente submitted |
| F-35 Remove slack stub | Fase 0 pulizia | Era fraudolentemente submitted |
| F-37 Remove LiteLLM | Fase 0 pulizia | Era fraudolentemente submitted |
| F-38 Remove dummy.ts/dist | Fase 0 pulizia | Era fraudolentemente submitted |

## Competitive analysis

### vs mesh-llm (michaelneale/mesh-llm)
- mesh-llm = distributed inference (GPU pooling). Convergio = agent orchestration.
- Orthogonal: mesh-llm potrebbe essere un inference provider per Convergio.
- Da rubare: subprocess plugin model (crash isolation), blackboard gossip, Nostr discovery.
- Nostro vantaggio: full orchestration, persistent state, governance, multi-provider.

### vs claw-code / oh-my-codex / openclaw
- Nessuno ha: Extension system, semantic manifest, org-as-package, dependency validation.
- Nostro differenziatore: rete di organizzazioni autonome con marketplace.

## Pre-condizioni: ConvergioPlatform cleanup

### 6 worktree con 29 commit non mergiati (plan 10056)

| Worktree | Commit | Contenuto |
|----------|-------:|-----------|
| cvg-w1-security | 1 | Mesh auth, host spoofing, RBAC |
| cvg-w2-bugfix | 6 | F-08 to F-15 (PowerGuard, watchdog, kernel_ask) |
| cvg-w3-hardening | 5 | F-16, F-19, F-20, F-21, F-23 (unwrap, budget, rate limit, spawn_blocking) |
| cvg-w4-kernel | 5 | F-24 to F-28 (write_intent, EscalateToAli, Apple Silicon) |
| cvg-w5-meshreg | 3 | F-30, F-31, F-33 (merge_env, sanitize, token sync) |
| cvg-w6-cleanup | 9 | F-34 to F-40, F-71, F-72 (email/slack stubs, litellm, scripts) |

**Merge order**: w1 → w2 → w3 → w4 → w5 → w6 (possibili conflitti)
**Da fare PRIMA di migrare codice al nuovo repo.**

### 5 stash da valutare
- stash@{0}: WIP on v20.5.0 plan status
- stash@{1-2}: WIP on v20.5.0
- stash@{3}: WIP on evidence gate
- stash@{4}: plan-10022 leftovers

Probabilmente tutti obsoleti → `git stash drop` dopo verifica.

### Repo cruft (non-daemon)
CommandCenter/, dashboard_web/, demo/, dist/, coverage/, plans/, types/dummy.ts,
convergio-architecture.html, daemon.log, NEXT_SESSION.md, PARITY.md

### Nuovo repo creato
- GitHub: https://github.com/Roberdan/convergio (pubblico)
- Locale: /Users/Roberdan/GitHub/convergio
- Struttura workspace iniziata: daemon/Cargo.toml + convergio-types (Extension trait, Manifest, DomainEvent, errors)
- Manca: CLAUDE.md, Constitution, Manifesto, Cargo.toml dei crate rimanenti, .gitignore

### Licenza e documenti da copiare nel nuovo repo
- Copiare `/Users/Roberdan/GitHub/ConvergioPlatform/LICENSE` (Convergio Community License v1.3) → `/Users/Roberdan/GitHub/convergio/LICENSE` (sovrascrive la MIT creata da GitHub)
- Copiare `CONSTITUTION.md` → invariato
- Copiare `AgenticManifesto.md` → invariato
- Copiare `LEGAL_NOTICE.md` → invariato
- Copiare `CONTRIBUTING.md` → adattare ai workspace
- Copiare `SECURITY.md` → invariato
- Nel README del nuovo repo, sezione License deve contenere:

> **Convergio is free. The code is open. We trust you.**
>
> This project is released under the [**Convergio Community License**](./LICENSE) — a source-available license.
> The source code is public and readable, but commercial redistribution and hosted services require explicit permission.
>
> Always free, no questions asked: students, people with disabilities, non-profit organizations.
>
> If Convergio brings value to your work, consider supporting [FightTheStroke Foundation](https://fightthestroke.org).

## Prossime sessioni (ordine consigliato)

### Sessione Frontend: convergio-frontend backlog

Stato attuale (04 Aprile 2026): Plan 10059 + 10060 completati. CI verde su main. 100 componenti, 58 E2E, 96 unit tests.

#### Bug / Fix aperti

1. **Mobile search** — `SearchCombobox` è `hidden md:flex`, su mobile non c'è modo di cercare. Serve un bottone hamburger/search che apra il combobox su mobile (overlay full-screen o drawer).

2. **Manettino responsive** — container fisso 160×160px, non scala su schermi <400px. Servono breakpoint o CSS `scale()` per adattarsi.

3. **SteppedRotary (Engine)** — stessi problemi del Manettino originale: container 100×100px fisso, knob/label overlap su mobile. Verificare con il design originale `controls-ferrari-dials.ts` e allineare.

4. **Lint warnings** — 13 warning attivi (nessun error):
   - `_request` unused in `proxy.ts`
   - `allSrc` unused in `generate-component-docs.ts`
   - `Copy` unused in `icons/page.tsx`
   - Vari `@next/next/no-img-element` in avatar
   - Fare un pass di cleanup

5. **Dashboard page (convergio.yaml mode)** — la pagina `/` quando usa `convergio.yaml` (non `maranello.yaml`) punta a un dashboard con API calls al daemon. Senza daemon attivo, le API crashano. Servirebbero fallback/loading states robusti.

#### Documentazione

6. **Props documentation** — solo 4/100 MDX hanno documentazione manuale completa (mn-chat, mn-chart, mn-dashboard, mn-swot). Le altre 96 sono auto-generate con prop descriptions inferite dal nome/tipo. Pass manuale per i 20 componenti più usati.

7. **MDX `allSrc` warning** — il generatore `generate-component-docs.ts` ha una variabile `allSrc` inutilizzata (leggeva .helpers.ts ma non lo usa). Rimuovere.

8. **convergio.yaml vs maranello.yaml** — documentare chiaramente nel README quale usare quando: `maranello.yaml` per design system standalone, `convergio.yaml` per la piattaforma completa con daemon.

#### UI / UX miglioramenti

9. **Showcase category pages** — i demo components non hanno tutti la stessa qualità. Alcune categorie (ops, network) hanno demo minimali. Aggiungere ComponentDoc wrapper con props table a tutte.

10. **Theme playground** — `/showcase/themes` mostra solo un subset di componenti. Aggiungere più componenti per verificare cross-theme rendering.

11. **A11y FAB** — OpenDyslexic caricato da CDN. Considerare bundling locale per offline/privacy.

12. **Keyboard navigation** — il SearchCombobox supporta ArrowUp/Down/Enter/Escape ma non Tab per muoversi tra gruppi. Aggiungere.

13. **E2E coverage** — 58 test coprono tutte le pagine ma non testano interazioni complesse (search, theme switch via combobox, Manettino click). Aggiungere interaction tests.

#### Architettura

14. **Old `command-menu.tsx` refs** — file cancellato, ma `CommandDialog` in `ui/command.tsx` è ancora esportato e inutilizzato. Valutare se rimuovere o tenere come primitivo shadcn.

15. **Config-driven vs hardcoded nav** — la sidebar in `layout.tsx` hardcoda i 12 category links. Dovrebbe leggere da `maranello.yaml` (il YAML ha già la nav completa). Il config-loader supporta già `navigation.sections`.

16. **`page-renderer.tsx` blocks** — il renderer supporta 17 block types ma solo una manciata sono testati con dati reali dal YAML. Verificare che tutti funzionino con dati di esempio.

### Sessione A: Merge worktree ConvergioPlatform
1. Merge 6 worktree in ordine su main
2. Verificare cargo check + cargo test
3. Pulire worktree e stash
4. Questo allinea main all'ultimo stato del lavoro fatto

### Sessione B: Setup nuovo repo convergio
1. Completare CLAUDE.md per nuovo repo
2. Copiare Constitution + Manifesto
3. Creare Cargo.toml per tutti i crate (stub)
4. Verificare `cargo check` workspace vuoto
5. Scrivere .gitignore
6. Push iniziale

### Sessione C+: Migrazione crate per crate
1. Fase 0: pulizia (TUI, stubs) — su ConvergioPlatform, poi migra il pulito
2. Fase 1-10: un crate per sessione, dal tracker

## Riferimenti conversazione (per sessioni future)

Questa sessione (03 Aprile 2026) ha coperto:
1. Analisi monolite daemon: 129K righe, 905 file, 43 tabelle sparse
2. Riconciliazione piano 10056: 25 task promossi done, 4 fraudolenti, 13 bloccati
3. Decisione cancellazione TUI (10.2K righe, zero utenti)
4. Architettura 3-layer: infrastruttura → servizi piattaforma → extension
5. Extension Contract: Rust trait + HTTP bridge per qualsiasi linguaggio
6. Manifest semantico con SemVer per auto-regolazione
7. DB ownership per modulo con migrazioni portabili
8. Domain Events per osservabilità real-time con nomi umani
9. Org-as-Package: marketplace di organizzazioni installabili con sandboxing
10. Sicurezza: firma pacchetti, sandbox runtime, token scoped per org
11. Kernel ridefinito: non core, è Jarvis come Extension
12. Inference routing: decisione di business per-org, non infrastruttura
13. UI: CRUD completo, SSE events, OpenAPI auto-gen — tutto pronto per convergio-frontend
14. Decisione nuovo repo con migrazione chirurgica
15. Identità nominale: tutto ha un nome umano, non ID
16. Long-running execution: heartbeat, checkpoint, resume, budget guard
17. Inter-org communication: delegazioni con verifica permessi e budget

Tracker: ~/Desktop/WORKSPACE-SPLIT.md (questo file)
Memory: ~/.claude/projects/.../memory/project_workspace_split_vision.md

### Sessione 04 Aprile 2026 (convergio-frontend) — riepilogo

1. Continuazione Plan 10059/10060 — tutti 17 task completati e validati da Thor
2. Creato CI pipeline GitHub Actions (PR #6): typecheck → lint → build → 96 unit → 58 E2E
3. Riscritto README.md con schema YAML completo, architettura aggiornata, documentazione
4. Rigenerato 96/100 MDX con esempi realistici e prop descriptions (script migliorato)
5. Fix command palette: da modale centrata → inline SearchCombobox ancorata alla search bar
6. Fix Manettino: portato dimensioni originali da convergio-design (160×160, knob 64, ring 80)
7. Fix sidebar: aggiunte 4 icone mancanti (Compass, LayoutGrid, TextCursorInput, Shapes)
8. Fix dashboard crash: API costs wrapping {costs:[]} → unwrap con useMemo
9. Cleanup: rimosso command-menu.tsx, .copilot-tracking/, .worktrees/
10. ESLint: aggiunto .worktrees/ a globalIgnores (eliminati 329 errori falsi)
11. Aggiornato convergio.yaml (rimosso /preview), maranello.yaml (nav completa con 12 categorie)
12. Fix guide docs: adding-a-theme.md paths corretti, aggiunto step Cmd-K
13. Stato finale: main pulito, CI verde, 0 lint errors, 58 E2E ✅, 96 unit ✅
