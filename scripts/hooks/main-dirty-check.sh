#!/usr/bin/env bash
# main-dirty-check.sh — WARNING when main repo has uncommitted changes.
# WHY: 2026-03-31 incident — copilot left 467 dirty files on main.
# Triggered by: SubagentStart hook.
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0

# Only check the main repo, not worktrees
COMMON=$(git -C "$REPO_ROOT" rev-parse --git-common-dir 2>/dev/null) || exit 0
GITDIR=$(git -C "$REPO_ROOT" rev-parse --git-dir 2>/dev/null) || exit 0
[ "$COMMON" != "$GITDIR" ] && exit 0

DIRTY=$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null | grep -c "^ M\|^M \|^??" || true)
if [ "${DIRTY:-0}" -gt 5 ]; then
  BRANCH=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null)
  echo "WARNING: Main repo has $DIRTY dirty files on '$BRANCH'." >&2
  echo "Possible crashed agent. Verify PRs, then: git checkout -- . && git clean -fd" >&2
fi

exit 0
