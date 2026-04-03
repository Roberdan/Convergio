#!/bin/bash
set -euo pipefail

# Run phases sequentially, each in its own worktree.
# Merges PR after each phase, then moves to the next.
# Usage: ./scripts/chain-fasi.sh
#
# Stops on first failure. Safe to leave unattended.

REPO="/Users/Roberdan/GitHub/convergio"
SCRIPT="$REPO/scripts/launch-fase.sh"
LOG="$REPO/.worktrees/chain.log"

mkdir -p "$REPO/.worktrees"

# ============================================================
# CHAIN ORDER — edit this list
# Format: "phase:crate"
# ============================================================
CHAIN=(
    "11:inference"
    "12:prompt"
    "12b:agent-prompts"
    "12c:agent-catalog"
)

log() {
    local msg="[$(date '+%H:%M:%S')] $*"
    echo "$msg"
    echo "$msg" >> "$LOG"
}

wait_for_pr_merge() {
    local pr_number="$1"
    log "Waiting for PR #$pr_number CI to pass..."

    # Wait for checks to complete
    while true; do
        local status
        status=$(gh pr checks "$pr_number" --repo Roberdan/convergio 2>/dev/null | grep -c "pass" || echo "0")
        local total
        total=$(gh pr checks "$pr_number" --repo Roberdan/convergio 2>/dev/null | wc -l | tr -d ' ')

        if [ "$total" -gt 0 ] && [ "$status" -eq "$total" ]; then
            log "PR #$pr_number — all $total checks passed"
            break
        fi

        local fail
        fail=$(gh pr checks "$pr_number" --repo Roberdan/convergio 2>/dev/null | grep -c "fail" || echo "0")
        if [ "$fail" -gt 0 ]; then
            log "ERROR: PR #$pr_number has failing checks. Stopping chain."
            exit 1
        fi

        sleep 30
    done

    # Merge
    log "Merging PR #$pr_number..."
    gh pr merge "$pr_number" --merge --delete-branch --repo Roberdan/convergio
    log "PR #$pr_number merged."

    # Update main
    cd "$REPO"
    git checkout main 2>/dev/null
    git pull origin main
}

log "=== Chain started: ${CHAIN[*]} ==="

for entry in "${CHAIN[@]}"; do
    IFS=':' read -r phase crate <<< "$entry"
    log "--- Fase $phase ($crate) ---"

    WORKTREE="$REPO/.worktrees/fase-$phase"

    # Create worktree from latest main
    cd "$REPO"
    git checkout main 2>/dev/null
    git pull origin main

    if [ -d "$WORKTREE" ]; then
        git worktree remove "$WORKTREE" --force 2>/dev/null || true
    fi
    git worktree add "$WORKTREE" main

    # Launch Claude in worktree
    cd "$WORKTREE"
    git checkout -b "feat/fase-$phase-$crate"

    PROMPT="Leggi ~/Desktop/WORKSPACE-SPLIT.md TUTTO prima di fare qualsiasi cosa.

Fai Fase $phase: convergio-$crate.
Vecchio repo sorgente: /Users/Roberdan/GitHub/ConvergioPlatform
Nuovo repo worktree: $WORKTREE (sei GIA' in un worktree isolato, NON crearne un altro)

OBBLIGATORIO:
- Sei già nel worktree giusto e sul branch feat/fase-$phase-$crate
- Segui la checklist di chiusura fase nel tracker
- Alla fine: commit, push, crea PR con gh pr create
- Controlla e risolvi i commenti di review sulla PR
- NON mergiare la PR — lo fa lo script che ti ha lanciato"

    log "Launching Claude for fase $phase..."
    claude --dangerously-skip-permissions -p "$PROMPT" 2>&1 | tee "$REPO/.worktrees/fase-$phase.log"

    # Find the PR that was created
    PR_NUMBER=$(gh pr list --head "feat/fase-$phase-$crate" --repo Roberdan/convergio --json number -q '.[0].number' 2>/dev/null || echo "")

    if [ -z "$PR_NUMBER" ]; then
        log "ERROR: No PR found for fase $phase. Claude may have failed. Stopping chain."
        exit 1
    fi

    log "PR #$PR_NUMBER created for fase $phase"
    wait_for_pr_merge "$PR_NUMBER"

    # Cleanup worktree
    cd "$REPO"
    git worktree remove "$WORKTREE" --force 2>/dev/null || true

    log "--- Fase $phase done ---"
done

log "=== Chain complete ==="
