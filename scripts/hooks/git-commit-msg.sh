#!/usr/bin/env bash
set -euo pipefail

# Git commit-msg hook: G5 conventional commits.
# Install: ln -sf ../../scripts/hooks/git-commit-msg.sh .git/hooks/commit-msg

MSG_FILE="$1"
MSG=$(head -1 "$MSG_FILE")

VALID="feat|fix|docs|chore|refactor|test|ci|perf|build|style|revert"
if ! echo "$MSG" | grep -qE "^(${VALID})(\([^)]+\))?!?:[[:space:]].+"; then
  echo "BLOCKED: G5 CommitLint — '$MSG'" >&2
  echo "Format: type(scope): message" >&2
  echo "Types: $VALID" >&2
  exit 1
fi

exit 0
