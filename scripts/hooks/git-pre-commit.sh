#!/usr/bin/env bash
set -euo pipefail

# Git pre-commit hook for convergio repo.
# Enforces: G1 (MainGuard), G2 (FileSizeGuard), G3 (SecretScan), G4 (SqliteBlock)
# Install: ln -sf ../../scripts/hooks/git-pre-commit.sh .git/hooks/pre-commit

# G1: No commits on main
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
COMMON=$(git rev-parse --git-common-dir 2>/dev/null)
GITDIR=$(git rev-parse --git-dir 2>/dev/null)
if [ "$COMMON" = "$GITDIR" ] && { [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; }; then
  echo "BLOCKED: G1 MainGuard — cannot commit on $BRANCH. Use a worktree." >&2
  exit 1
fi

# G2: Max 250 lines per file (.rs/.ts/.js/.sh)
STAGED=$(git diff --cached --name-only --diff-filter=ACM)
for f in $STAGED; do
  case "$f" in *.rs|*.ts|*.js|*.sh)
    if [ -f "$f" ]; then
      LINES=$(wc -l < "$f")
      if [ "$LINES" -gt 250 ]; then
        echo "BLOCKED: G2 FileSizeGuard — $f has $LINES lines (max 250)." >&2
        exit 1
      fi
    fi
  ;; esac
done

# G3: No secrets in code
for f in $STAGED; do
  if [ -f "$f" ]; then
    if grep -qEi '(ANTHROPIC_API_KEY|OPENAI_API_KEY|sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|password\s*=\s*"[^"]{8,}")' "$f" 2>/dev/null; then
      echo "BLOCKED: G3 SecretScan — potential secret in $f." >&2
      exit 1
    fi
  fi
done

# G4: No sqlite3 direct usage
for f in $STAGED; do
  case "$f" in *.sh|*.py)
    if [ -f "$f" ] && grep -qE '(^|[;&[:space:]])sqlite3[[:space:]]' "$f" 2>/dev/null; then
      echo "BLOCKED: G4 SqliteBlock — direct sqlite3 in $f. Use cvg CLI." >&2
      exit 1
    fi
  ;; esac
done

exit 0
