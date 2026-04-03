#!/bin/bash
set -euo pipefail

REPO="/Users/Roberdan/GitHub/convergio"
LOG="$REPO/.worktrees/orchestrator.log"
PROMPT_FILE="$REPO/scripts/orchestrator-prompt.md"

mkdir -p "$REPO/.worktrees"

echo "[$(date)] Orchestrator starting" >> "$LOG"

cd "$REPO"

# -p takes prompt as argument (NOT stdin)
# Do NOT use </dev/null — it conflicts with -p
timeout 7200 claude --dangerously-skip-permissions \
    --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent" \
    --add-dir "$REPO" \
    --model claude-opus-4-6 \
    -p "$(cat "$PROMPT_FILE")" 2>&1 | tee -a "$LOG"

EXIT_CODE=$?
echo "[$(date)] Claude exited (code=$EXIT_CODE). Re-launching in 10s..." >> "$LOG"
sleep 10
exec "$0"
