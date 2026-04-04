#!/usr/bin/env bash
# pre-compaction-snapshot.sh — PreCompact hook.
# Saves plan state before context compaction.
set -euo pipefail

if command -v cvg &>/dev/null; then
  cvg checkpoint save-auto 2>/dev/null || true
fi

exit 0
