#!/usr/bin/env bash
# test_daemon_builds.sh — verify convergio-daemon compiles and unit tests pass
set -euo pipefail

cleanup() {
  echo "[test_daemon_builds] cleanup complete"
}
trap cleanup EXIT

DAEMON_DIR="$HOME/GitHub/convergio-daemon"

echo "[test_daemon_builds] checking cargo check..."
cd "$DAEMON_DIR"
cargo check 2>&1 | tail -5
echo "[test_daemon_builds] cargo check PASS"

echo "[test_daemon_builds] running cargo test --lib..."
cargo test --lib 2>&1 | tail -20
echo "[test_daemon_builds] cargo test --lib PASS"

echo "[test_daemon_builds] ALL PASS"
