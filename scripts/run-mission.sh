#!/usr/bin/env bash
set -euo pipefail

# Convergio autonomous mission runner.
# Launches Claude sessions that read MISSION.md and execute.
# When a session ends (context full or task done), restarts automatically.
# Ctrl+C to stop.

REPO="/Users/Roberdan/GitHub/convergio"
MAX_ITERATIONS=20
ITERATION=0

cd "$REPO"

echo "╔══════════════════════════════════════════╗"
echo "║  Convergio Mission Runner                ║"
echo "║  Max iterations: $MAX_ITERATIONS                  ║"
echo "║  Ctrl+C to stop                          ║"
echo "╚══════════════════════════════════════════╝"

while [ "$ITERATION" -lt "$MAX_ITERATIONS" ]; do
    ITERATION=$((ITERATION + 1))
    echo ""
    echo "━━━ Iteration $ITERATION/$MAX_ITERATIONS — $(date) ━━━"
    echo ""

    # Pull latest changes (other agents may have pushed)
    git pull origin main --ff-only 2>/dev/null || true

    # Rebuild daemon if code changed
    if [ -f daemon/target/release/convergio ]; then
        DAEMON_AGE=$(( $(date +%s) - $(stat -f %m daemon/target/release/convergio) ))
        if [ "$DAEMON_AGE" -gt 300 ]; then
            echo "Rebuilding daemon..."
            (cd daemon && cargo build --release 2>/dev/null)
            launchctl unload ~/Library/LaunchAgents/com.convergio.daemon.plist 2>/dev/null
            sleep 1
            launchctl load ~/Library/LaunchAgents/com.convergio.daemon.plist
            sleep 2
        fi
    fi

    # Launch Claude with mission
    timeout 7200 claude \
        --dangerously-skip-permissions \
        --model claude-opus-4-6 \
        --max-turns 200 \
        -p "Leggi MISSION.md. Poi esegui. Quando il contesto si riempie, aggiorna WORKSPACE-SPLIT.md e termina." \
        2>&1 | tee "/tmp/convergio-mission-$ITERATION.log"

    EXIT_CODE=$?
    echo ""
    echo "Session $ITERATION ended (exit code: $EXIT_CODE)"

    # Check if mission is complete
    if grep -q "Step 5.*DONE\|Self-hosting.*DONE\|MISSION COMPLETE" WORKSPACE-SPLIT.md 2>/dev/null; then
        echo "🎉 MISSION COMPLETE!"
        break
    fi

    # Brief pause before next iteration
    sleep 10
done

echo ""
echo "Mission runner finished after $ITERATION iterations."
