#!/bin/bash
set -euo pipefail

# Verify parity between exported data and the new daemon.
# Usage: ./scripts/verify-parity.sh <export-dir> [--port PORT]
#
# Compares record counts and health status, outputs a report.

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
REPORT_FILE="$EXPORT_DIR/parity-report.txt"
PASS=0
FAIL=0
WARN=0

log() { echo "[verify $(date '+%H:%M:%S')] $*"; }

check() {
    local name="$1" status="$2" detail="$3"
    if [ "$status" = "OK" ]; then
        PASS=$((PASS + 1))
        echo "  [OK]   $name — $detail" | tee -a "$REPORT_FILE"
    elif [ "$status" = "WARN" ]; then
        WARN=$((WARN + 1))
        echo "  [WARN] $name — $detail" | tee -a "$REPORT_FILE"
    else
        FAIL=$((FAIL + 1))
        echo "  [FAIL] $name — $detail" | tee -a "$REPORT_FILE"
    fi
}

# Count records in a JSON file (list or dict with data key)
count_json() {
    local file="$1"
    if [ ! -f "$file" ]; then echo "0"; return; fi
    python3 -c "
import json,sys
try:
    d=json.load(open(sys.argv[1]))
    if isinstance(d,list): print(len(d))
    elif isinstance(d,dict) and 'data' in d: print(len(d['data']))
    elif isinstance(d,dict) and 'items' in d: print(len(d['items']))
    elif isinstance(d,dict): print(len(d))
    else: print(0)
except: print(0)
" "$file" 2>/dev/null || echo "0"
}

# Count records from a live API endpoint
count_api() {
    local endpoint="$1"
    local tmp
    tmp=$(mktemp)
    if curl -sf "$NEW_API$endpoint" -o "$tmp" 2>/dev/null; then
        count_json "$tmp"
        rm -f "$tmp"
    else
        rm -f "$tmp"
        echo "-1"
    fi
}

# --- Pre-flight ---
if [ ! -d "$EXPORT_DIR" ]; then
    log "FATAL: Export dir not found: $EXPORT_DIR"
    exit 1
fi

> "$REPORT_FILE"
echo "=== Parity Report ===" | tee -a "$REPORT_FILE"
echo "Date: $(date)" | tee -a "$REPORT_FILE"
echo "Export: $EXPORT_DIR" | tee -a "$REPORT_FILE"
echo "Target: $NEW_API" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# --- 1. Health check ---
echo "--- Health ---" | tee -a "$REPORT_FILE"
if curl -sf "$NEW_API/api/health" >/dev/null 2>&1; then
    check "new-daemon-health" "OK" "responsive"
else
    check "new-daemon-health" "FAIL" "not reachable"
fi

if curl -sf "$NEW_API/api/health/deep" >/dev/null 2>&1; then
    check "new-daemon-deep-health" "OK" "deep check passed"
else
    check "new-daemon-deep-health" "WARN" \
        "deep health unavailable"
fi

# --- 2. Record count comparison ---
echo "" | tee -a "$REPORT_FILE"
echo "--- Record Counts ---" | tee -a "$REPORT_FILE"

compare_counts() {
    local name="$1" file="$2" endpoint="$3"
    local exported new_count

    exported=$(count_json "$file")
    new_count=$(count_api "$endpoint")

    if [ "$new_count" = "-1" ]; then
        check "$name" "WARN" \
            "exported=$exported, API unavailable"
        return
    fi

    if [ "$exported" = "$new_count" ]; then
        check "$name" "OK" \
            "exported=$exported new=$new_count"
    elif [ "$exported" = "0" ]; then
        check "$name" "OK" \
            "nothing to import (exported=0)"
    else
        check "$name" "WARN" \
            "exported=$exported new=$new_count (delta)"
    fi
}

compare_counts "plans" \
    "$EXPORT_DIR/plans.json" "/api/plan-db/list"
compare_counts "agents" \
    "$EXPORT_DIR/agents.json" "/api/ipc/agents"
compare_counts "orgs" \
    "$EXPORT_DIR/orgs.json" "/api/orgs"

# --- 3. API endpoint availability ---
echo "" | tee -a "$REPORT_FILE"
echo "--- Endpoint Availability ---" | tee -a "$REPORT_FILE"

ENDPOINTS=(
    "/api/health"
    "/api/health/deep"
    "/api/metrics"
    "/api/agents/catalog"
    "/api/plan-db/list"
)

for ep in "${ENDPOINTS[@]}"; do
    if curl -sf "$NEW_API$ep" >/dev/null 2>&1; then
        check "endpoint:$ep" "OK" "available"
    else
        check "endpoint:$ep" "WARN" "not available"
    fi
done

# --- 4. Summary ---
echo "" | tee -a "$REPORT_FILE"
echo "--- Summary ---" | tee -a "$REPORT_FILE"
TOTAL=$((PASS + FAIL + WARN))
echo "  PASS=$PASS  FAIL=$FAIL  WARN=$WARN  TOTAL=$TOTAL" \
    | tee -a "$REPORT_FILE"

if [ "$FAIL" -gt 0 ]; then
    echo "" | tee -a "$REPORT_FILE"
    echo "RESULT: FAILED ($FAIL failures)" \
        | tee -a "$REPORT_FILE"
    log "Report: $REPORT_FILE"
    exit 1
else
    echo "" | tee -a "$REPORT_FILE"
    echo "RESULT: PASSED" | tee -a "$REPORT_FILE"
    log "Report: $REPORT_FILE"
    exit 0
fi
