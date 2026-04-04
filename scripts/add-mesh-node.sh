#!/usr/bin/env bash
set -euo pipefail

HOSTNAME="${1:-}"

if [[ -z "${HOSTNAME}" ]]; then
    echo "Usage: $0 <hostname>" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="/Users/Roberdan/GitHub/convergio/daemon/target/release/convergio"
PLIST_SRC="${SCRIPT_DIR}/com.convergio.daemon.plist"
PLIST_NAME="com.convergio.daemon.plist"
REMOTE_BINARY_DIR="/usr/local/bin"
REMOTE_LAUNCH_AGENTS="${HOME}/Library/LaunchAgents"
REMOTE_BINARY="${REMOTE_BINARY_DIR}/convergio"

# Verify local binary exists
if [[ ! -f "${BINARY}" ]]; then
    echo "ERROR: binary not found at ${BINARY}" >&2
    echo "Run 'cargo build --release' first." >&2
    exit 1
fi

# Verify SSH connectivity
echo "Checking SSH connectivity to ${HOSTNAME}..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "${HOSTNAME}" "echo ok" &>/dev/null; then
    echo "ERROR: cannot connect to ${HOSTNAME} via SSH." >&2
    echo "Ensure SSH keys are configured and the host is reachable." >&2
    exit 1
fi
echo "SSH OK."

# Copy binary
echo "Copying binary to ${HOSTNAME}:${REMOTE_BINARY}..."
scp "${BINARY}" "${HOSTNAME}:${REMOTE_BINARY}"
ssh "${HOSTNAME}" "chmod +x ${REMOTE_BINARY}"

# Copy plist
echo "Copying plist to ${HOSTNAME}:${REMOTE_LAUNCH_AGENTS}/${PLIST_NAME}..."
ssh "${HOSTNAME}" "mkdir -p ${REMOTE_LAUNCH_AGENTS}"
scp "${PLIST_SRC}" "${HOSTNAME}:${REMOTE_LAUNCH_AGENTS}/${PLIST_NAME}"

# Install service on remote
echo "Installing service on ${HOSTNAME}..."
ssh "${HOSTNAME}" "launchctl unload ${REMOTE_LAUNCH_AGENTS}/${PLIST_NAME} 2>/dev/null || true"
ssh "${HOSTNAME}" "launchctl load ${REMOTE_LAUNCH_AGENTS}/${PLIST_NAME}"

echo "Mesh node ${HOSTNAME} configured and service started."
