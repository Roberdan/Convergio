#!/bin/bash
set -euo pipefail

# Export data from the old Convergio daemon via its API.
# Usage: ./scripts/export-old-data.sh [--port PORT]
#
# Exports plans, tasks, agents, orgs, and audit log as JSON files
# into ~/.convergio/migration/export-{timestamp}/

OLD_PORT="${OLD_PORT:-8420}"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --port) OLD_PORT="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

OLD_API="http://localhost:${OLD_PORT}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
EXPORT_DIR="$HOME/.convergio/migration/export-${TIMESTAMP}"

log() { echo "[export $(date '+%H:%M:%S')] $*"; }
fail() { log "FATAL: $*"; exit 1; }

# --- Pre-flight ---
log "=== Export from old daemon ($OLD_API) ==="

if ! curl -sf "$OLD_API/api/health" >/dev/null 2>&1; then
    fail "Old daemon not reachable at $OLD_API"
fi

mkdir -p "$EXPORT_DIR"
log "Export dir: $EXPORT_DIR"

# --- Helper: export one endpoint ---
export_endpoint() {
    local name="$1" endpoint="$2" file="$3"
    log "Exporting $name ..."
    if curl -sf "$OLD_API$endpoint" -o "$file" 2>/dev/null; then
        if python3 -c "import json,sys; json.load(open(sys.argv[1]))" \
            "$file" 2>/dev/null; then
            local count
            count=$(python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
if isinstance(d,list): print(len(d))
elif isinstance(d,dict) and 'data' in d: print(len(d['data']))
elif isinstance(d,dict): print(len(d))
else: print('?')
" "$file" 2>/dev/null || echo "?")
            log "  $name: $count records -> $(basename "$file")"
        else
            log "  WARNING: $name returned invalid JSON"
            rm -f "$file"
        fi
    else
        log "  WARNING: $name endpoint not available ($endpoint)"
        echo "[]" > "$file"
    fi
}

# --- Export all data types ---
export_endpoint "health"  "/api/health" \
    "$EXPORT_DIR/health.json"
export_endpoint "plans"   "/api/plan-db/list" \
    "$EXPORT_DIR/plans.json"
export_endpoint "agents"  "/api/ipc/agents" \
    "$EXPORT_DIR/agents.json"
export_endpoint "orgs"    "/api/orgs" \
    "$EXPORT_DIR/orgs.json"
export_endpoint "audit"   "/api/audit/log" \
    "$EXPORT_DIR/audit.json"

# --- Also grab per-org details if orgs exist ---
ORGS_FILE="$EXPORT_DIR/orgs.json"
if [ -f "$ORGS_FILE" ]; then
    ORG_IDS=$(python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
items = d if isinstance(d,list) else d.get('data',d.get('orgs',[]))
if isinstance(items,list):
    for o in items:
        oid=o.get('id',o.get('slug',''))
        if oid: print(oid)
" "$ORGS_FILE" 2>/dev/null || true)

    if [ -n "$ORG_IDS" ]; then
        mkdir -p "$EXPORT_DIR/orgs"
        for oid in $ORG_IDS; do
            export_endpoint "org:$oid" "/api/orgs/$oid" \
                "$EXPORT_DIR/orgs/${oid}.json"
        done
    fi
fi

# --- Summary ---
log "=== Export summary ==="
TOTAL_FILES=$(find "$EXPORT_DIR" -name '*.json' | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$EXPORT_DIR" | cut -f1)
log "Files: $TOTAL_FILES  Size: $TOTAL_SIZE"
log "Path: $EXPORT_DIR"

# Write manifest for import script
python3 -c "
import json, os, sys
d = '$EXPORT_DIR'
manifest = {'timestamp': '$TIMESTAMP', 'source': '$OLD_API', 'files': {}}
for f in os.listdir(d):
    if f.endswith('.json') and f != 'manifest.json':
        path = os.path.join(d, f)
        try:
            data = json.load(open(path))
            if isinstance(data, list):
                manifest['files'][f] = len(data)
            elif isinstance(data, dict):
                manifest['files'][f] = len(data)
        except: pass
json.dump(manifest, open(os.path.join(d, 'manifest.json'), 'w'), indent=2)
" 2>/dev/null || true

log "=== Export complete ==="
echo "$EXPORT_DIR"
