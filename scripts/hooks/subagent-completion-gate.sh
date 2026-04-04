#!/usr/bin/env bash
# subagent-completion-gate.sh — SubagentStop safety net.
# Catches: uncommitted work, auth failures, missing evidence.
# WHY: ~30% of subagents exhaust tool budget before git commit.
set -euo pipefail

INPUT=$(cat)
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null)
LAST_MSG=$(echo "$INPUT" | jq -r '.last_assistant_message // empty' 2>/dev/null)

# --- EvidenceGate: warn on "done" without evidence ---
CLAIMS_DONE=false
EVIDENCE_FOUND=false

if echo "$LAST_MSG" | grep -qiE '\b(done|completed|submitted|finished)\b'; then
  CLAIMS_DONE=true
fi
if echo "$LAST_MSG" | grep -qiE 'cargo test|test result|tests passed|passing|curl.*output|exit 0|ok \([0-9]+ test'; then
  EVIDENCE_FOUND=true
fi
if $CLAIMS_DONE && ! $EVIDENCE_FOUND; then
  echo "WARNING: EvidenceGate — agent claims done but no test evidence found." >&2
fi

# --- Auth failure detection ---
if echo "$LAST_MSG" | grep -qiE "401|unauthorized|auth.*fail"; then
  echo '{"decision":"block","reason":"Auth failure detected. Check tokens."}'
  exit 0
fi

# --- AgentIdentity warning ---
if [ -z "${CONVERGIO_AGENT_NAME:-}" ]; then
  echo "WARNING: CONVERGIO_AGENT_NAME not set. Run: cvg agent start <name>" >&2
fi

# --- Auto-commit uncommitted work in worktree ---
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
[ -z "$ROOT" ] && exit 0

SHORT_ID="${AGENT_ID:0:8}"
WORKTREE=""
for wt in "$ROOT/.claude/worktrees"/agent-"$SHORT_ID"* "$ROOT/.worktrees"/agent-"$SHORT_ID"*; do
  [ -d "$wt" ] && WORKTREE="$wt" && break
done
[ -z "$WORKTREE" ] && exit 0

DIRTY=$(cd "$WORKTREE" && git status --porcelain 2>/dev/null | head -1)
if [ -n "$DIRTY" ]; then
  cd "$WORKTREE"
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  git add -A 2>/dev/null
  git commit -m "fix: auto-commit uncommitted subagent work ($BRANCH)

Agent $AGENT_ID exhausted budget before committing.
Auto-committed by subagent-completion-gate.sh.

Co-Authored-By: subagent-completion-gate <noreply@convergio.dev>" 2>/dev/null || true
  echo "AUTO-COMMITTED: Agent $AGENT_ID work saved in $WORKTREE" >&2
fi

exit 0
