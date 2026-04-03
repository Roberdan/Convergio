#!/bin/bash
set -euo pipefail

# Cutover: stop old daemon, start new daemon on same port.
# Usage: ./scripts/cutover.sh [--dry-run]
#
# Prerequisites:
# - New daemon built: cd daemon && cargo build --release
# - Old daemon running on port 8420

OLD_DAEMON_API="http://localhost:8420"
NEW_BINARY="./daemon/target/release/convergio"
CONFIG_PATH="$HOME/.convergio/config.toml"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DRY_RUN=false

[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# 1. Pre-flight checks
log "=== Pre-flight ==="

if [ ! -f "$NEW_BINARY" ]; then
    log "ERROR: New binary not found. Run: cd daemon && cargo build --release"
    exit 1
fi

log "New binary: $NEW_BINARY ($(du -h "$NEW_BINARY" | cut -f1))"

# Check old daemon is running
if curl -sf "$OLD_DAEMON_API/api/health" >/dev/null 2>&1; then
    OLD_VERSION=$(curl -sf "$OLD_DAEMON_API/api/health" | python3 -c "import sys,json; print(json.load(sys.stdin).get('version','unknown'))" 2>/dev/null || echo "unknown")
    log "Old daemon running: v$OLD_VERSION"
else
    log "WARNING: Old daemon not running on $OLD_DAEMON_API"
fi

# 2. Export critical data from old daemon
log "=== Export from old daemon ==="

if curl -sf "$OLD_DAEMON_API/api/health" >/dev/null 2>&1; then
    EXPORT_DIR=$("$SCRIPT_DIR/export-old-data.sh" \
        --port 8420 | tail -1)
    log "Exported to $EXPORT_DIR"
else
    EXPORT_DIR="$HOME/.convergio/migration/export-none"
    mkdir -p "$EXPORT_DIR"
    log "Skipping export (old daemon not reachable)"
fi

if $DRY_RUN; then
    log "=== DRY RUN — stopping here ==="
    exit 0
fi

# 3. Stop old daemon
log "=== Stopping old daemon ==="

OLD_PID=$(lsof -ti :8420 2>/dev/null || echo "")
if [ -n "$OLD_PID" ]; then
    log "Sending SIGTERM to PID $OLD_PID"
    kill "$OLD_PID" 2>/dev/null || true
    sleep 2
    # Force kill if still alive
    if kill -0 "$OLD_PID" 2>/dev/null; then
        log "Force killing PID $OLD_PID"
        kill -9 "$OLD_PID" 2>/dev/null || true
        sleep 1
    fi
    log "Old daemon stopped"
else
    log "No process on port 8420"
fi

# 4. Start new daemon
log "=== Starting new daemon ==="

CONVERGIO_CONFIG="$CONFIG_PATH" nohup "$NEW_BINARY" \
    >> "$HOME/.convergio/logs/daemon.log" 2>&1 &
NEW_PID=$!
log "New daemon started: PID $NEW_PID"

# 5. Wait for health
log "=== Waiting for health ==="
for i in $(seq 1 10); do
    if curl -sf "$OLD_DAEMON_API/api/health" >/dev/null 2>&1; then
        HEALTH=$(curl -sf "$OLD_DAEMON_API/api/health")
        log "HEALTHY: $HEALTH"
        break
    fi
    if [ "$i" -eq 10 ]; then
        log "ERROR: New daemon not healthy after 10s"
        log "Check logs: tail $HOME/.convergio/logs/daemon.log"
        exit 1
    fi
    sleep 1
done

# 6. Import data into new daemon
log "=== Import data ==="
if [ -d "$EXPORT_DIR" ] && [ -f "$EXPORT_DIR/plans.json" ]; then
    "$SCRIPT_DIR/import-new-data.sh" "$EXPORT_DIR" \
        --port 8420 || log "WARNING: import had errors"
else
    log "Skipping import (no export data)"
fi

# 7. Verify parity
log "=== Verification ==="
curl -sf "$OLD_DAEMON_API/api/health" \
    > "$EXPORT_DIR/health-new.json" 2>/dev/null || true

if [ -d "$EXPORT_DIR" ] && [ -f "$EXPORT_DIR/plans.json" ]; then
    "$SCRIPT_DIR/verify-parity.sh" "$EXPORT_DIR" \
        --port 8420 || log "WARNING: parity check had issues"
fi

log "New daemon health saved to $EXPORT_DIR/health-new.json"
log "Old data exported to $EXPORT_DIR/"
log ""
log "=== Cutover complete ==="
log "Old: v$OLD_VERSION -> New: v0.1.0"
log "Verify: curl $OLD_DAEMON_API/api/health"
log "Rollback: kill $NEW_PID && restart old daemon"
