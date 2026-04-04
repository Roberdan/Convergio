#!/usr/bin/env bash
set -euo pipefail

# Consolidated PreToolUse guard for convergio repo.
# Usage: echo '{"command":"..."}' | pre-tool-guard.sh <tool>
# Exit 0 = allow, Exit 2 = blocked (message on stderr)

TOOL="${1:-}"
INPUT=$(cat 2>/dev/null || true)

block() { echo "BLOCKED: $1" >&2; exit 2; }
warn()  { echo "WARNING: $1" >&2; }

cmd()        { echo "$INPUT" | jq -r '.command // empty' 2>/dev/null || echo "$INPUT"; }
file_path()  { echo "$INPUT" | jq -r '.file_path // empty' 2>/dev/null; }
new_string() { echo "$INPUT" | jq -r '.new_string // empty' 2>/dev/null; }

guard_bash() {
  local CMD
  CMD=$(cmd)
  [ -z "$CMD" ] && return 0

  # sqlite3 direct — use cvg CLI or daemon API
  if echo "$CMD" | grep -qE '(^|[;&[:space:]])sqlite3[[:space:]]'; then
    block "Never use sqlite3 directly — use cvg CLI or daemon API"
  fi

  # CommitLint: conventional commit format
  if echo "$CMD" | grep -qE '(^|[;&[:space:]])git[[:space:]]+commit.*-m'; then
    local MSG
    MSG=$(echo "$CMD" | sed -n "s/.*-m[[:space:]]*['\"]\\{0,1\\}//p" | sed "s/['\"].*//")
    if [ -n "$MSG" ]; then
      local VALID_TYPES="feat|fix|docs|chore|refactor|test|ci|perf|build|style|revert"
      if ! echo "$MSG" | grep -qE "^(${VALID_TYPES})(\([^)]+\))?!?:[[:space:]].+"; then
        block "CommitLint: message must match 'type(scope): message'. Got: $MSG"
      fi
    fi
  fi

  # EvidenceGate: mark test runs
  if echo "$CMD" | grep -qE \
     '(^|[;&[:space:]])(cargo[[:space:]]+test|npx[[:space:]]+vitest|pytest|bats)'; then
    touch "/tmp/.convergio-test-ran" 2>/dev/null || true
  fi

  # EvidenceGate: block commit of code files without recent test run
  if echo "$CMD" | grep -qE '(^|[;&[:space:]])git[[:space:]]+commit'; then
    STAGED_CODE=$(git diff --cached --name-only 2>/dev/null \
      | grep -cE '\.(rs|ts|py|sh)$' 2>/dev/null || echo 0)
    if [ "${STAGED_CODE}" -gt 0 ]; then
      MARKER="/tmp/.convergio-test-ran"
      if [ ! -f "${MARKER}" ]; then
        block "EvidenceGate: no test run detected. Run cargo test first."
      fi
      if command -v find >/dev/null 2>&1; then
        FRESH=$(find "${MARKER}" -mmin -10 2>/dev/null | wc -l | tr -d ' ')
        if [ "${FRESH}" = "0" ]; then
          block "EvidenceGate: test marker older than 10 min. Re-run tests."
        fi
      fi
    fi
  fi
}

guard_edit() {
  local FILE
  FILE=$(file_path)
  [ -z "$FILE" ] && return 0

  # FailLoud: warn on silent fallback patterns in Rust
  if echo "$FILE" | grep -qE '\.rs$'; then
    local NS
    NS=$(new_string)
    if echo "$NS" | grep -qE 'unwrap_or_default\(\)'; then
      warn "FailLoud: unwrap_or_default() silently swallows errors. Use expect() or ?."
    fi
    if echo "$NS" | grep -qE 'let[[:space:]]+_[[:space:]]*='; then
      warn "FailLoud: 'let _ = ...' discards a Result. Handle the error explicitly."
    fi
  fi
}

case "$TOOL" in
  bash) guard_bash ;;
  edit) guard_edit ;;
  *)    ;;
esac
