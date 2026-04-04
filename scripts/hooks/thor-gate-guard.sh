#!/usr/bin/env bash
# thor-gate-guard.sh — Enforce correct plan execution workflow.
# Constitution Article VI, ADR-0001: ONLY Thor can set task status=done.
# Flow: pending → in_progress → submitted (executor) → done (Thor only)
# Triggered by: PreToolUse Bash hook.
set -euo pipefail

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null)
[ -z "$CMD" ] && exit 0

# Block: cvg task update <id> done
if echo "$CMD" | grep -qE 'cvg\s+task\s+update\s+\S+\s+done'; then
  echo "BLOCKED: ThorGateGuard — cannot set task status=done directly." >&2
  echo "  ONLY Thor can promote tasks to done." >&2
  echo "  Use: cvg task update <id> submitted" >&2
  echo "  Then: cvg plan validate <plan_id>" >&2
  exit 2
fi

# Block: per-task validate
if echo "$CMD" | grep -qE 'cvg\s+task\s+validate'; then
  echo "BLOCKED: ThorGateGuard — validate at wave level, not per-task." >&2
  echo "  Use: cvg plan validate <plan_id>" >&2
  exit 2
fi

# Block: forced-admin validate endpoint
if echo "$CMD" | grep -qE '/api/plans/[0-9]+/validate'; then
  echo "BLOCKED: ThorGateGuard — use cvg plan validate <plan_id>." >&2
  exit 2
fi

# Block: direct SQL/API status=done
if echo "$CMD" | grep -qiE "UPDATE.*tasks.*SET.*status.*=.*['\"]done['\"]"; then
  echo "BLOCKED: ThorGateGuard — cannot set done via SQL." >&2
  exit 2
fi
if echo "$CMD" | grep -qE 'curl.*status.*done.*task|curl.*task.*status.*done'; then
  echo "BLOCKED: ThorGateGuard — cannot set done via API." >&2
  exit 2
fi

exit 0
