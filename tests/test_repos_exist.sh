#!/usr/bin/env bash
# test_repos_exist.sh — verify all convergio ecosystem repos exist
set -euo pipefail

cleanup() {
  echo "[test_repos_exist] cleanup complete"
}
trap cleanup EXIT

GITHUB_DIR="$HOME/GitHub"
REPOS=(convergio-daemon convergio-app convergio-web convergio)

fail=0
for repo in "${REPOS[@]}"; do
  if [[ -d "$GITHUB_DIR/$repo" ]]; then
    echo "[test_repos_exist] PASS: $repo exists at $GITHUB_DIR/$repo"
  else
    echo "[test_repos_exist] FAIL: $repo NOT found at $GITHUB_DIR/$repo"
    fail=1
  fi
done

if [[ $fail -ne 0 ]]; then
  echo "[test_repos_exist] FAILED: one or more repos missing"
  exit 1
fi

echo "[test_repos_exist] ALL PASS"
