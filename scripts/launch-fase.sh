#!/bin/bash
set -euo pipefail

# Launch a phase in an isolated worktree with Claude Code
# Usage: ./scripts/launch-fase.sh <phase-number> <crate-name> [next-phase] [next-crate]
#
# Examples:
#   ./scripts/launch-fase.sh 9 server
#   ./scripts/launch-fase.sh 9 server 14 http-bridge   # auto-chains to phase 14 after

PHASE="${1:?Usage: launch-fase.sh <phase> <crate> [next-phase] [next-crate]}"
CRATE="${2:?Usage: launch-fase.sh <phase> <crate> [next-phase] [next-crate]}"
NEXT_PHASE="${3:-}"
NEXT_CRATE="${4:-}"

REPO="/Users/Roberdan/GitHub/convergio"
WORKTREE="$REPO/.worktrees/fase-$PHASE"
TRACKER="$HOME/Desktop/WORKSPACE-SPLIT.md"

echo "=== Fase $PHASE ($CRATE) ==="

# 1. Create worktree
cd "$REPO"
if [ -d "$WORKTREE" ]; then
    echo "Worktree already exists at $WORKTREE — reusing"
else
    git worktree add "$WORKTREE" main
    echo "Created worktree at $WORKTREE"
fi

# 2. Launch Claude in the worktree
cd "$WORKTREE"

PROMPT="Leggi ~/Desktop/WORKSPACE-SPLIT.md TUTTO prima di fare qualsiasi cosa.

Fai Fase $PHASE: convergio-$CRATE.
Vecchio repo sorgente: /Users/Roberdan/GitHub/ConvergioPlatform
Nuovo repo worktree: $WORKTREE (sei GIA' in un worktree isolato)

OBBLIGATORIO:
- Sei già nel worktree giusto, NON crearne un altro
- Crea branch: git checkout -b feat/fase-$PHASE-$CRATE
- Segui la checklist di chiusura fase nel tracker
- Alla fine: commit, push, PR, controlla commenti review"

claude --dangerously-skip-permissions -p "$PROMPT"

echo "=== Fase $PHASE completata ==="

# 3. Auto-chain to next phase if specified
if [ -n "$NEXT_PHASE" ] && [ -n "$NEXT_CRATE" ]; then
    echo "=== Chaining to Fase $NEXT_PHASE ($NEXT_CRATE) ==="
    exec "$REPO/scripts/launch-fase.sh" "$NEXT_PHASE" "$NEXT_CRATE"
fi
