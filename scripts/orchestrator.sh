#!/bin/bash
set -euo pipefail

REPO="/Users/Roberdan/GitHub/convergio"
LOG="$REPO/.worktrees/orchestrator.log"

mkdir -p "$REPO/.worktrees"

echo "[$(date)] Orchestrator starting" >> "$LOG"

cd "$REPO"

# IMPORTANT: short prompt that tells Claude to READ the full prompt from file.
# Long prompts passed as -p argument cause silent hangs.
# This pattern works reliably in tmux and background execution.
timeout 7200 claude --dangerously-skip-permissions \
    --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent" \
    --add-dir "$REPO" \
    --model claude-opus-4-6 \
    -p "Sei l'orchestratore di convergio. Leggi scripts/orchestrator-prompt.md per le istruzioni complete, poi leggi ~/Desktop/WORKSPACE-SPLIT.md per lo stato. Inizia a lavorare: controlla PR aperte, worktree attivi, e lancia/monitora le fasi. Se il contesto si riempie scrivi lo stato in ~/Desktop/ORCHESTRATOR-STATE.md e rilancia: cd $REPO && nohup ./scripts/orchestrator.sh >> .worktrees/orchestrator.log 2>&1 &" \
    2>&1 | tee -a "$LOG"

EXIT_CODE=$?
echo "[$(date)] Claude exited (code=$EXIT_CODE). Re-launching in 10s..." >> "$LOG"
sleep 10
exec "$0"
