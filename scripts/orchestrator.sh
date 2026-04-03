#!/bin/bash
set -euo pipefail

REPO="/Users/Roberdan/GitHub/convergio"
LOG="$REPO/.worktrees/orchestrator.log"
PROMPT_FILE="$REPO/scripts/orchestrator-prompt.md"

mkdir -p "$REPO/.worktrees"

echo "[$(date)] Orchestrator starting" >> "$LOG"

cd "$REPO"
PROMPT=$(cat "$PROMPT_FILE")

claude --dangerously-skip-permissions -p "$PROMPT" 2>&1 | tee -a "$LOG"

echo "[$(date)] Claude exited. Re-launching in 10s..." >> "$LOG"
sleep 10
exec "$0"
