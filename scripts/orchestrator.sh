#!/bin/bash
set -euo pipefail

REPO="/Users/Roberdan/GitHub/convergio"
LOG="$REPO/.worktrees/orchestrator.log"
PROMPT_FILE="$REPO/scripts/orchestrator-prompt.md"

mkdir -p "$REPO/.worktrees"

echo "[$(date)] Orchestrator starting" >> "$LOG"

cd "$REPO"

# Key fixes from research:
# 1. </dev/null — prevents stdin hang in tmux
# 2. --allowedTools — explicit tool permissions
timeout 7200 claude -p \
    --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent" \
    --add-dir "$REPO" \
    --model claude-opus-4-6 \
    "$(cat "$PROMPT_FILE")" </dev/null 2>&1 | tee -a "$LOG"

EXIT_CODE=$?
echo "[$(date)] Claude exited (code=$EXIT_CODE). Re-launching in 10s..." >> "$LOG"
sleep 10
exec "$0"
