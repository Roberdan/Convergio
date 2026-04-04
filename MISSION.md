# Convergio — Mission Orders

Questo file è il comando operativo per ogni sessione Claude.
Leggilo. Eseguilo. Aggiorna WORKSPACE-SPLIT.md. Non inventare.

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
5. Fase 31: File transport (rsync tra nodi)
6. Fase 37b: Node capability registry (GPU, voice, compute)
7. Fase 34: Delegation orchestrator (rsync + remote spawn + sync + notify)
8. Fase 35: E2E integration test

### Step 3: Completamento
9. Fase 36b: Inference reale (Ollama/API, non echo)
10. Fase 39b: Progetti non-codice (report, business docs)
11. Fase 40b: Integration test HTTP (830 unit + E2E)
12. Frontend: rifare convergio-frontend dentro Convergio
    - Spawnare agenti via daemon (sara-ux, jony, nasra, baccio)
    - Admin + monitoring completo
    - Repo: /Users/Roberdan/GitHub/convergio-frontend

### Step 4: Self-hosting
13. Fase 26: Convergio costruisce convergio

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
