#!/usr/bin/env bash
set -euo pipefail

PLIST_NAME="com.convergio.daemon.plist"
PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/${PLIST_NAME}"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
PLIST_DEST="${LAUNCH_AGENTS_DIR}/${PLIST_NAME}"
BINARY="/Users/Roberdan/GitHub/convergio/daemon/target/release/convergio"
FIREWALL="/usr/libexec/ApplicationFirewall/socketfilterfw"

# Verify binary exists
if [[ ! -f "${BINARY}" ]]; then
    echo "ERROR: binary not found at ${BINARY}" >&2
    echo "Run 'cargo build --release' first." >&2
    exit 1
fi

# Ensure LaunchAgents directory exists
mkdir -p "${LAUNCH_AGENTS_DIR}"

# Install plist
echo "Installing ${PLIST_NAME} to ${LAUNCH_AGENTS_DIR}..."
cp "${PLIST_SRC}" "${PLIST_DEST}"

# Unload if already loaded (ignore errors if not loaded)
launchctl unload "${PLIST_DEST}" 2>/dev/null || true

# Load service
echo "Loading service..."
launchctl load "${PLIST_DEST}"

# Add binary to macOS Application Firewall
if [[ -x "${FIREWALL}" ]]; then
    echo "Adding binary to firewall allowlist..."
    sudo "${FIREWALL}" --add "${BINARY}"
    sudo "${FIREWALL}" --unblockapp "${BINARY}"
else
    echo "WARNING: socketfilterfw not found, skipping firewall registration." >&2
fi

echo "Service installed and started."
echo "Logs: /tmp/convergio-daemon.log"
echo "Errors: /tmp/convergio-daemon.err"
