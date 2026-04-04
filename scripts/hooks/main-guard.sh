#!/usr/bin/env bash
# main-guard.sh — BLOCK writes to daemon/ when on the main branch.
# WHY: 2026-03-31 incident — copilot dirtied 467 files on main directly.
# Triggered by: PreToolUse Edit/Write hooks.
set -euo pipefail

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.file_path // .input.file_path // empty' 2>/dev/null)
[ -z "$FILE" ] && exit 0

# Guard daemon source, tests, scripts, and config
echo "$FILE" | grep -qE "daemon/|scripts/|\.claude/" || exit 0

# Check if we're in the main repo on the main branch
TOPLEVEL=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
BRANCH=$(git -C "$TOPLEVEL" rev-parse --abbrev-ref HEAD 2>/dev/null) || exit 0

# Allow if we're in a worktree (not the main checkout)
COMMON=$(git -C "$TOPLEVEL" rev-parse --git-common-dir 2>/dev/null) || exit 0
GITDIR=$(git -C "$TOPLEVEL" rev-parse --git-dir 2>/dev/null) || exit 0
[ "$COMMON" != "$GITDIR" ] && exit 0

if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "BLOCKED: MainGuard — cannot modify $FILE on branch '$BRANCH'." >&2
  echo "Create a worktree: git worktree add --detach .worktrees/<name> HEAD" >&2
  exit 2
fi

exit 0
