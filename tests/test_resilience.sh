#!/usr/bin/env bash
# test_resilience.sh — verify daemon/src/resilience/ has all required modules
set -euo pipefail

cleanup() {
  echo "[test_resilience] cleanup complete"
}
trap cleanup EXIT

RESILIENCE_DIR="$HOME/GitHub/convergio-daemon/src/resilience"

REQUIRED_MODULES=(
  circuit_breaker
  retry
  health
  reaper
  checkpoint
  notify
  watchdog
)

fail=0
for module in "${REQUIRED_MODULES[@]}"; do
  file="$RESILIENCE_DIR/${module}.rs"
  if [[ -f "$file" ]]; then
    echo "[test_resilience] PASS: ${module}.rs exists"
  else
    echo "[test_resilience] FAIL: ${module}.rs NOT found at $file"
    fail=1
  fi
done

if [[ $fail -ne 0 ]]; then
  echo "[test_resilience] FAILED: one or more resilience modules missing"
  exit 1
fi

echo "[test_resilience] ALL PASS"
