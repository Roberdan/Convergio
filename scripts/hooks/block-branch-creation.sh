#!/usr/bin/env bash
# block-branch-creation.sh — Enforce worktree discipline.
# WHY: All work must happen in worktrees. Branches are managed by the
#      release pipeline to prevent accidental branch pollution.
# Triggered by: PreToolUse Bash hook.
set -euo pipefail

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null)
[ -z "$CMD" ] && exit 0

# Allow: git branch listing/delete
if echo "$CMD" | grep -qE 'git branch[[:space:]]*(-[dD]|-v|--list|-a|-r|$)'; then
  exit 0
fi

# Allow: git worktree add --detach
if echo "$CMD" | grep -q 'git worktree add'; then
  if echo "$CMD" | grep -q -- '--detach'; then
    exit 0
  fi
  echo "BLOCKED: 'git worktree add' without --detach creates a branch." >&2
  echo "Use: git worktree add --detach <path> HEAD" >&2
  exit 2
fi

# Block: branch creation patterns
if echo "$CMD" | grep -qE 'git (branch [^-]|checkout -b|switch -c|switch --create)'; then
  echo "BLOCKED: Branch creation is forbidden. Use worktrees:" >&2
  echo "  git worktree add --detach .worktrees/<name> HEAD" >&2
  echo "  cd .worktrees/<name> && git checkout -b feat/<name>" >&2
  exit 2
fi

exit 0
