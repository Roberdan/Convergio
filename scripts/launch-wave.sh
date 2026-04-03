#!/bin/bash
set -euo pipefail

# Launch multiple phases in parallel, each in its own terminal tab
# Usage: ./scripts/launch-wave.sh
#
# Edit the PHASES array below to configure what to launch.
# Each entry: "phase_number:crate_name"
#
# Supports: Ghostty, iTerm2, Terminal.app, or plain tmux

REPO="/Users/Roberdan/GitHub/convergio"
SCRIPT="$REPO/scripts/launch-fase.sh"

# ============================================================
# CONFIGURE PHASES TO LAUNCH HERE
# Format: "phase:crate" or "phase:crate:next_phase:next_crate" for chaining
# ============================================================
PHASES=(
    "9:server"
    "10:kernel"       # extensions — one per crate if you want max parallelism
    "11:inference"
    "12:prompt"
)

launch_in_tmux() {
    local session="convergio-wave"
    tmux kill-session -t "$session" 2>/dev/null || true

    local first=true
    for entry in "${PHASES[@]}"; do
        IFS=':' read -r phase crate next_phase next_crate <<< "$entry"
        local cmd="$SCRIPT $phase $crate ${next_phase:-} ${next_crate:-}"

        if $first; then
            tmux new-session -d -s "$session" -n "fase-$phase" "$cmd; read -p 'Done. Press enter to close.'"
            first=false
        else
            tmux new-window -t "$session" -n "fase-$phase" "$cmd; read -p 'Done. Press enter to close.'"
        fi
    done

    tmux attach -t "$session"
}

launch_in_osascript() {
    # Works with Terminal.app, iTerm2, Ghostty (anything that responds to AppleScript)
    for entry in "${PHASES[@]}"; do
        IFS=':' read -r phase crate next_phase next_crate <<< "$entry"
        local cmd="$SCRIPT $phase $crate ${next_phase:-} ${next_crate:-}"

        osascript -e "
            tell application \"Terminal\"
                activate
                do script \"$cmd\"
            end tell
        " 2>/dev/null || {
            echo "AppleScript failed, falling back to background launch"
            $cmd &
        }
    done
}

# Detect terminal and launch
if command -v tmux &>/dev/null && [ -z "${TERM_PROGRAM:-}" ]; then
    echo "Launching ${#PHASES[@]} phases in tmux..."
    launch_in_tmux
else
    echo "Launching ${#PHASES[@]} phases in separate terminal windows..."
    launch_in_osascript
fi

echo ""
echo "=== Wave launched ==="
echo "Monitor with: git worktree list"
echo "Check PRs with: gh pr list"
