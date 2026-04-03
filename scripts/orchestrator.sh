#!/bin/bash
set -euo pipefail

# Convergio build orchestrator — a Claude that manages other Claudes.
# Reads the tracker, figures out what's done/pending/in-progress,
# launches phases in the right order, monitors PRs, and re-launches
# itself if context fills up.
#
# Usage: ./scripts/orchestrator.sh
# Leave it running. It does everything.

REPO="/Users/Roberdan/GitHub/convergio"
LOG="$REPO/.worktrees/orchestrator.log"
STATE="$REPO/.worktrees/orchestrator-state.json"
TRACKER="$HOME/Desktop/WORKSPACE-SPLIT.md"

mkdir -p "$REPO/.worktrees"

PROMPT="$(cat <<'PROMPT_EOF'
Sei l'orchestratore di convergio. Il tuo lavoro è costruire il progetto fase per fase, in modo autonomo.

## Come funzioni

1. Leggi ~/Desktop/WORKSPACE-SPLIT.md per capire lo stato (fasi completate, in corso, da fare)
2. Controlla le PR aperte: `gh pr list --repo Roberdan/convergio`
3. Controlla i worktree attivi: `git worktree list` dentro /Users/Roberdan/GitHub/convergio
4. Decidi cosa fare:
   - Se ci sono PR aperte → controlla CI status con `gh pr checks <N>`, controlla commenti con `gh api repos/Roberdan/convergio/pulls/<N>/comments`. Se CI verde e nessun commento aperto → mergia con `gh pr merge <N> --merge --delete-branch`
   - Se ci sono fasi in corso (worktree attivi) → aspetta, controlla ogni 2 minuti
   - Se ci sono fasi pronte (deps soddisfatte, nessun worktree attivo per quella fase) → lancia la prossima

## Come lanciare una fase

```bash
cd /Users/Roberdan/GitHub/convergio
git pull origin main
git worktree add .worktrees/fase-<N> main
cd .worktrees/fase-<N>
git checkout -b feat/fase-<N>-<crate>
```

Poi lancia Claude nel worktree:
```bash
cd /Users/Roberdan/GitHub/convergio/.worktrees/fase-<N>
claude --dangerously-skip-permissions -p "<prompt per la fase>"
```

Il prompt per la fase deve dire:
- Leggi ~/Desktop/WORKSPACE-SPLIT.md TUTTO
- Fai Fase N: convergio-<crate>
- Vecchio repo: /Users/Roberdan/GitHub/ConvergioPlatform
- Sei già nel worktree, NON crearne un altro
- Sei già sul branch feat/fase-N-crate
- Segui la checklist di chiusura
- Commit, push, crea PR, controlla commenti review
- NON mergiare — lo fai tu (orchestratore)

## Grafo dipendenze (cosa può partire quando)

```
DONE: 1-8 (types, telemetry, db, security, ipc, mesh, orchestrator, cli)
WAVE C: 9 (server) + 10 (extensions) — possono essere in corso
WAVE D: 11 (inference) + 12 (prompt) — partono dopo wave C o in parallelo se deps ok
POST-12: 12b (migrate prompts) → 12c (agent catalog)
POST-13: 13 (org-package) → 13b (project scaffolding)
WAVE E: 14-18 — dopo wave D
WAVE F: 19-20 — dopo tutto
```

Fasi 11 e 12 possono partire ORA se 9 e 10 non le bloccano (e non le bloccano — deps diverse).

## Regole

- MAI lanciare due fasi che toccano lo stesso crate
- MAI mergiare PR con CI rossa o commenti non risolti
- Massimo 3 fasi parallele (per non saturare la macchina)
- Dopo ogni merge: `git pull origin main` prima di creare il prossimo worktree
- Aggiorna il tracker dopo ogni fase completata
- Se il tuo contesto si sta riempiendo (>60 turni): scrivi lo stato in ~/Desktop/ORCHESTRATOR-STATE.md (cosa è done, cosa è in corso, cosa è next) e lancia un nuovo te stesso:
  ```bash
  cd /Users/Roberdan/GitHub/convergio
  nohup ./scripts/orchestrator.sh >> .worktrees/orchestrator.log 2>&1 &
  ```

## Adesso

1. Controlla lo stato: PR aperte, worktree attivi, fasi completate
2. Se fasi 9/10 sono in corso → monitora. Se hanno PR → controlla CI e mergia.
3. Lancia le prossime fasi pronte
4. Loop: monitora → mergia → lancia → monitora

Vai.
PROMPT_EOF
)"

echo "[$(date)] Orchestrator starting" >> "$LOG"
echo "[$(date)] Launching Claude orchestrator..." >> "$LOG"

cd "$REPO"
claude --dangerously-skip-permissions -p "$PROMPT" 2>&1 | tee -a "$LOG"

# If Claude exits (context full), re-launch
echo "[$(date)] Claude exited. Re-launching in 10s..." >> "$LOG"
sleep 10
exec "$0"
