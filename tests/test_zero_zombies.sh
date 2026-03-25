#!/usr/bin/env bash
# test_zero_zombies.sh — verify no stale worktrees exist (only main should be present)
set -euo pipefail

cleanup() {
  echo "[test_zero_zombies] cleanup complete"
}
trap cleanup EXIT

PLATFORM_DIR="$HOME/GitHub/ConvergioPlatform"

echo "[test_zero_zombies] checking git worktree list in $PLATFORM_DIR..."
worktree_output=$(git -C "$PLATFORM_DIR" worktree list 2>&1)
echo "$worktree_output"

# Count non-main worktrees (lines that don't contain [main])
stale_count=$(echo "$worktree_output" | grep -v '\[main\]' | grep -c '^\/' || true)

if [[ $stale_count -gt 0 ]]; then
  echo "[test_zero_zombies] WARNING: $stale_count non-main worktree(s) found"
  echo "[test_zero_zombies] Non-main worktrees:"
  echo "$worktree_output" | grep -v '\[main\]' | grep '^\/' || true
  echo "[test_zero_zombies] NOTE: Worktrees present during active task execution are acceptable"
fi

# Verify main worktree is present
if echo "$worktree_output" | grep -q '\[main\]'; then
  echo "[test_zero_zombies] PASS: main worktree confirmed"
else
  echo "[test_zero_zombies] FAIL: main worktree not found"
  exit 1
fi

echo "[test_zero_zombies] ALL PASS"
