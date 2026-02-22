#!/usr/bin/env bash
set -euo pipefail

staged_files=$(git diff --cached --name-only --diff-filter=ACM)

if [[ -z "$staged_files" ]]; then
  exit 0
fi

secret_pattern='(api_key|api-key|apikey|password|token|secret)[[:space:]]*[:=][[:space:]]*["'"'"'`]?[A-Za-z0-9_\-]{8,}'

if git diff --cached -- "$@" | grep -E -i "$secret_pattern" >/dev/null; then
  echo "ERROR: Potential secret detected in staged changes."
  echo "Remove secrets before committing."
  exit 1
fi

exit 0
