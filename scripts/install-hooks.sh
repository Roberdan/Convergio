#!/bin/bash
# 🚀 Convergio Git Hooks Installation Script

set -e

echo "🔧 Installing Convergio Git Hooks..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$ROOT_DIR/.githooks"
GIT_HOOKS_DIR="$ROOT_DIR/.git/hooks"

# Check if we're in a git repository
if [[ ! -d "$ROOT_DIR/.git" ]]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Create git hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Install pre-commit hook
if [[ -f "$HOOKS_DIR/pre-commit" ]]; then
    cp "$HOOKS_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
    chmod +x "$GIT_HOOKS_DIR/pre-commit"
    echo "✅ Pre-commit hook installed"
else
    echo "⚠️  Warning: pre-commit hook not found in $HOOKS_DIR"
fi

# Set git hooks path (optional, for custom hooks directory)
git config core.hooksPath .githooks

echo "🎉 Git hooks installation completed!"
echo ""
echo "📋 Installed hooks:"
echo "  - pre-commit: Auto-updates version on each commit"
echo ""
echo "🔄 To test the pre-commit hook:"
echo "  git add ."
echo "  git commit -m 'test: version auto-update'"
echo ""
echo "🚫 To skip hooks (not recommended):"
echo "  git commit --no-verify -m 'message'"