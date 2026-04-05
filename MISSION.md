# Convergio — Mission Orders

Questo file è il comando operativo per ogni sessione (Claude, Copilot, o altro).
Leggi prima AGENTS.md (regole universali), poi questo file (cosa fare), poi WORKSPACE-SPLIT.md (dettagli).

## Come lanciare

```bash
cd /Users/Roberdan/GitHub/convergio && claude
```

Prompt:

```
Leggi MISSION.md e WORKSPACE-SPLIT.md. Poi esegui.
```

## Obiettivo

Convergio deve essere un sistema COMPLETO e FUNZIONANTE per organizzazioni AI autonome.
Non un set di crate che compilano. Non un API layer passivo. Un sistema che:
- Riceve un problema → pianifica → esegue → valida → completa → notifica
- Tutto visibile nella UI in tempo reale
- Tutto tracciato nel DB (costi, tempi, learnings)
- Tutto auditabile post-facto

## Stato attuale

Leggi `WORKSPACE-SPLIT.md` per lo stato dettagliato.
Il daemon gira come servizio launchd su :8420. Token: `Bearer dev-local`.
CLI: `cvg status`, `cvg plan list`, `cvg cheatsheet`.

## Cosa fare — in ordine, NON saltare

### Step 0: IL LOOP DEVE CHIUDERSI
Senza questo il sistema sembra morto anche quando funziona.

1. **Fase 32b**: Agent→Plan lifecycle. Il monitor DEVE:
   - Aggiornare task status → submitted quando agente committa
   - Emettere TaskCompleted via DomainEventSink
   - Il reactor avanza wave→done e piano→done automaticamente
   - Telegram notifica se configurato

2. **Fase 32c**: Planner E2E. Ogni piano DEVE:
   - Avere objective, motivation, requester (enforced dalla API)
   - Ogni task con input/output/acceptance criteria
   - Ultimo task di ogni wave = integration test
   - POST /api/plan-db/validate rifiuta piani incompleti

3. **Fase 32d**: Thor piano-level:
   - Pre-review: quando piano → in_progress, Thor verifica completezza
   - Post-review: quando tutti task submitted, Thor verifica evidence
   - Se Thor trova problemi → piano bloccato, feedback al planner

**VERIFICA**: Roberto deve VEDERE nella UI i piani che si aggiornano.
Non passare a Step 1 senza questa verifica.

### Step 1: Fondamenta
4. Fase 23e: Wire DepgraphExtension in main.rs

### Step 2: Delegation pipeline
5. Fase 48: Node provisioning (sync config/memory/keys/binary a nodi remoti)
6. Fase 31: File transport (rsync tra nodi)
7. Fase 37b: Node capability registry (GPU, voice, compute)
8. Fase 34: Delegation orchestrator (rsync + remote spawn + sync + notify)
9. Fase 35: E2E integration test

### Step 3: Completamento
9. Fase 51: MLX diretto + TurboQuant (inference locale senza Ollama, context 128K)
10. Fase 52: Kernel/Jarvis su M1 Pro (voice, Telegram, watchdog locale)
11. Frontend: rifare convergio-frontend dentro Convergio

### Step 3b: Ottimizzazione continua
12. Fase 50: Autoresearch loop (ottimizzazione notturna codice + token, modelli locali)
13. Fase 47: ADR + docs

### Step 4: Production hardening (Wave I — gia' implementato sessione 6-8)
Fasi 41-46 completate. Vedi sezione 4 nel WORKSPACE-SPLIT.md.

### NOTA sulla Fase 49 (Harness Engineering)
NON duplicare nel filesystem quello che sta nel DB. Il DB ha gia' plans/tasks
(= feature_list), agent_activity (= progress), plan_metadata (= learnings).
L'agente legge dal DB via context API (32e), non da file .md statici.
Tenere: baseline test obbligatorio, Thor separato, una feature alla volta.

### Step 5: Self-hosting
19. Fase 26: Convergio costruisce convergio

## Prima cosa da fare in ogni nuova sessione

Se WORKSPACE-SPLIT.md non è ancora ristrutturato (>2200 righe):
1. Leggi RESTRUCTURE-INSTRUCTIONS.md
2. Ristruttura secondo la struttura target
3. Poi riprendi dall'ordine sopra

## Come lavorare — delega il più possibile

**Tu (la sessione Claude principale) sei il COORDINATORE, non l'esecutore.**
Il tuo contesto è prezioso — non sprecarlo a scrivere codice meccanico.

1. **Usa il daemon** per spawnare agenti: `POST /api/agents/spawn` con tier appropriato
2. **Usa Copilot con Opus** per task meccanici nel worktree:
   ```bash
   cd .worktrees/<task> && gh copilot --model claude-opus-4-6
   ```
3. **Usa Agent tool** per task paralleli indipendenti (con `isolation: "worktree"`)
4. **Tu decidi**: cosa fare, in che ordine, chi delega a chi, cosa verificare
5. **Tu verifichi**: che il loop sia chiuso, che i test passino, che la UI mostri il risultato
6. **Tu documenti**: aggiorna WORKSPACE-SPLIT.md con stato, learnings, decisioni

**Regola del contesto**: se un task richiede >50 righe di codice e non richiede
decisioni architetturali → delegalo. Se richiede decisioni → fallo tu.

## Long-run: quando il contesto si riempie, spawna te stesso

NON fermarti. NON chiedere a Roberto di rilanciare. Fai tu:

1. Aggiorna WORKSPACE-SPLIT.md con lo stato esatto (cosa hai fatto, cosa manca)
2. Spawna un nuovo agente via daemon con le istruzioni di continuare:
   ```bash
   curl -X POST -H "Authorization: Bearer dev-local" -H "Content-Type: application/json" \
     -d '{
       "agent_name": "mission-continuator",
       "org_id": "convergio",
       "instructions": "Leggi MISSION.md. Poi esegui. Riprendi da dove si è fermata la sessione precedente. Quando il contesto si riempie, spawna un nuovo te stesso e ripeti.",
       "tier": "t1",
       "budget_usd": 50.0,
       "timeout_secs": 7200
     }' http://localhost:8420/api/agents/spawn
   ```
3. Termina la tua sessione

Il daemon si occupa di: worktree, monitor, push, PR. Il nuovo agente legge MISSION.md,
vede lo stato in WORKSPACE-SPLIT.md, e riprende. Nessun intervento umano necessario.

## Regole NON negoziabili

1. **Loop chiuso** (Regola 10): ogni feature deve avere input→output→feedback→stato→visibile all'utente
2. **4 domande prima di ogni fase**: Chi produce input? Chi consuma output? Come l'utente lo vede? Come il sistema registra che è fatto?
3. **Worktree isolati**: mai lavorare su main. Un worktree = un branch = una PR
4. **Max 250 righe per file**
5. **cargo check + cargo test + cargo fmt** prima di ogni commit
6. **Smoke test E2E** dopo ogni fase (curl al daemon, verifica nella UI)
7. **Non dichiarare done** senza evidence verificabile
8. **Aggiorna WORKSPACE-SPLIT.md** dopo ogni fase completata
9. **Quando il contesto si riempie**: aggiorna il tracker, poi di' a Roberto di lanciare una nuova sessione
10. **No squash merge** — solo merge commit (enforced dal repo)

## Cosa NON fare

- NON costruire pezzi sconnessi (Learning #16 — pattern ricorrente)
- NON dichiarare done senza che il loop sia chiuso
- NON creare crate/moduli senza wirare nel daemon
- NON saltare step — l'ordine è deliberato
- NON risolvere problemi con workaround — fixa la root cause
- NON rileggere file già letti nella stessa sessione

## Risorse

| Cosa | Dove |
|------|------|
| Tracker completo | `WORKSPACE-SPLIT.md` |
| Regole | CONSTITUTION.md nella root |
| Vecchio repo | `/Users/Roberdan/GitHub/ConvergioPlatform` |
| Frontend | `/Users/Roberdan/GitHub/convergio-frontend` |
| Config | `claude-config/` |
| Daemon binary | `daemon/target/release/convergio` |
| CLI binary | `~/.local/bin/cvg` |
| Daemon logs | `/tmp/convergio-daemon.log`, `/tmp/convergio-daemon.err` |
| Learnings | Sezione "Lezioni" in WORKSPACE-SPLIT.md |
