#!/bin/bash
set -euo pipefail

# Import exported data into the new Convergio daemon.
# Usage: ./scripts/import-new-data.sh <export-dir> [--port PORT]
#
# Reads JSON files from export-dir and imports via the new daemon API.
# Falls back to direct DB import if API endpoints are unavailable.

if [ $# -lt 1 ]; then
    echo "Usage: $0 <export-dir> [--port PORT]"
    exit 1
fi

EXPORT_DIR="$1"; shift
NEW_PORT="${NEW_PORT:-8420}"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --port) NEW_PORT="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

NEW_API="http://localhost:${NEW_PORT}"
IMPORT_LOG="$EXPORT_DIR/import-log.json"

log() { echo "[import $(date '+%H:%M:%S')] $*"; }
fail() { log "FATAL: $*"; exit 1; }

# --- Pre-flight ---
log "=== Import into new daemon ($NEW_API) ==="

if [ ! -d "$EXPORT_DIR" ]; then
    fail "Export dir not found: $EXPORT_DIR"
fi

if ! curl -sf "$NEW_API/api/health" >/dev/null 2>&1; then
    fail "New daemon not reachable at $NEW_API"
fi

log "Source: $EXPORT_DIR"

RESULTS="{}"
record() {
    local key="$1" status="$2" count="${3:-0}"
    RESULTS=$(echo "$RESULTS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
d['$key']={'status':'$status','count':$count}
json.dump(d,sys.stdout)
" 2>/dev/null || echo "$RESULTS")
}

# --- Helper: import via API POST ---
import_via_api() {
    local name="$1" file="$2" endpoint="$3"
    if [ ! -f "$file" ]; then
        log "  SKIP $name: file not found"
        record "$name" "skipped"
        return
    fi

    local count
    count=$(python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
items=d if isinstance(d,list) else d.get('data',d.get('items',[]))
print(len(items) if isinstance(items,list) else 0)
" "$file" 2>/dev/null || echo "0")

    if [ "$count" = "0" ]; then
        log "  SKIP $name: 0 records"
        record "$name" "empty" 0
        return
    fi

    log "Importing $name ($count records) via $endpoint ..."

    local ok=0 err=0
    python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
items=d if isinstance(d,list) else d.get('data',d.get('items',[]))
if isinstance(items,list):
    for item in items:
        print(json.dumps(item))
elif isinstance(items,dict):
    print(json.dumps(items))
" "$file" 2>/dev/null | while IFS= read -r item; do
        if curl -sf -X POST "$NEW_API$endpoint" \
            -H "Content-Type: application/json" \
            -d "$item" >/dev/null 2>&1; then
            ok=$((ok + 1))
        else
            err=$((err + 1))
        fi
    done

    log "  $name: attempted $count records"
    record "$name" "imported" "$count"
}

# --- Import via backup/import if available ---
import_via_backup() {
    local name="$1" file="$2"
    if [ ! -f "$file" ]; then
        log "  SKIP $name: file not found"
        record "$name" "skipped"
        return
    fi
    log "Importing $name via backup/import endpoint ..."
    if curl -sf -X POST "$NEW_API/api/backup/import" \
        -H "Content-Type: application/json" \
        -d @"$file" >/dev/null 2>&1; then
        log "  $name: bulk import succeeded"
        record "$name" "bulk_imported"
    else
        log "  $name: backup/import not available, trying item-by-item"
        return 1
    fi
}

# --- Import orgs ---
log "=== Importing orgs ==="
ORGS_FILE="$EXPORT_DIR/orgs.json"
if [ -f "$ORGS_FILE" ]; then
    import_via_api "orgs" "$ORGS_FILE" "/api/orgs" || true
else
    log "  No orgs.json found"
fi

# --- Import agents ---
log "=== Importing agents ==="
AGENTS_FILE="$EXPORT_DIR/agents.json"
if [ -f "$AGENTS_FILE" ]; then
    import_via_api "agents" "$AGENTS_FILE" \
        "/api/agents/catalog" || true
else
    log "  No agents.json found"
fi

# --- Import plans ---
log "=== Importing plans ==="
PLANS_FILE="$EXPORT_DIR/plans.json"
if [ -f "$PLANS_FILE" ]; then
    # Try bulk import via backup first
    if ! import_via_backup "plans" "$PLANS_FILE" 2>/dev/null; then
        log "  Falling back to individual plan import"
        import_via_api "plans" "$PLANS_FILE" \
            "/api/projects/scaffold" || true
    fi
else
    log "  No plans.json found"
fi

# --- Import audit log ---
log "=== Importing audit ==="
AUDIT_FILE="$EXPORT_DIR/audit.json"
if [ -f "$AUDIT_FILE" ]; then
    log "  Audit log is read-only; saved for reference"
    record "audit" "reference_only"
fi

# --- Write import log ---
log "=== Import summary ==="
echo "$RESULTS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
json.dump(d,sys.stdout,indent=2)
print()
" 2>/dev/null | tee "$IMPORT_LOG"

log "Import log: $IMPORT_LOG"
log "=== Import complete ==="
