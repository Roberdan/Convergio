#!/bin/bash
#
# Convergio Web Platform - Version Bump Script
#
# Usage: ./scripts/bump-version.sh [major|minor|patch] [--no-commit]
#
# Examples:
#   ./scripts/bump-version.sh patch      # 3.0.0 -> 3.0.1
#   ./scripts/bump-version.sh minor      # 3.0.0 -> 3.1.0
#   ./scripts/bump-version.sh major      # 3.0.0 -> 4.0.0
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_ROOT/VERSION"
FRONTEND_PKG="$PROJECT_ROOT/frontend/package.json"
CHANGELOG="$PROJECT_ROOT/docs/CHANGELOG.md"

# Parse arguments
BUMP_TYPE="${1:-patch}"
NO_COMMIT=false
if [[ "$2" == "--no-commit" ]]; then
    NO_COMMIT=true
fi

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo -e "${RED}Error: Invalid bump type '$BUMP_TYPE'${NC}"
    echo "Usage: $0 [major|minor|patch] [--no-commit]"
    exit 1
fi

# Read current version
if [[ ! -f "$VERSION_FILE" ]]; then
    echo -e "${RED}Error: VERSION file not found${NC}"
    exit 1
fi

CURRENT_VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
echo -e "${BLUE}Current version: $CURRENT_VERSION${NC}"

# Parse version components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Calculate new version
case $BUMP_TYPE in
    major)
        NEW_MAJOR=$((MAJOR + 1))
        NEW_MINOR=0
        NEW_PATCH=0
        ;;
    minor)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$((MINOR + 1))
        NEW_PATCH=0
        ;;
    patch)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$MINOR
        NEW_PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="$NEW_MAJOR.$NEW_MINOR.$NEW_PATCH"
echo -e "${GREEN}New version: $NEW_VERSION${NC}"

# Update VERSION file
echo -e "${YELLOW}Updating VERSION file...${NC}"
echo "$NEW_VERSION" > "$VERSION_FILE"
echo -e "${GREEN}✓ VERSION file updated${NC}"

# Update package.json
echo -e "${YELLOW}Updating frontend/package.json...${NC}"
cd "$PROJECT_ROOT/frontend"
npm pkg set version="$NEW_VERSION" 2>/dev/null || {
    cd "$PROJECT_ROOT"
    jq ".version = \"$NEW_VERSION\"" "$FRONTEND_PKG" > tmp.json && mv tmp.json "$FRONTEND_PKG"
}
echo -e "${GREEN}✓ package.json updated${NC}"

# Update CHANGELOG
echo -e "${YELLOW}Adding CHANGELOG entry...${NC}"
TODAY=$(date +%Y-%m-%d)
CHANGELOG_ENTRY="## [$NEW_VERSION] - $TODAY

### Changed
- Version bump from $CURRENT_VERSION to $NEW_VERSION

---

"

# Insert new entry after the header
cd "$PROJECT_ROOT"
if grep -q "# Changelog" "$CHANGELOG"; then
    # Create temp file with new entry
    head -1 "$CHANGELOG" > /tmp/changelog_new.md
    echo "" >> /tmp/changelog_new.md
    echo "$CHANGELOG_ENTRY" >> /tmp/changelog_new.md
    tail -n +3 "$CHANGELOG" >> /tmp/changelog_new.md
    mv /tmp/changelog_new.md "$CHANGELOG"
    echo -e "${GREEN}✓ CHANGELOG.md updated${NC}"
else
    echo -e "${YELLOW}⚠ Could not find CHANGELOG header, skipping${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                    VERSION BUMP COMPLETE                       ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Previous version: ${YELLOW}$CURRENT_VERSION${NC}"
echo -e "  New version:      ${GREEN}$NEW_VERSION${NC}"
echo -e "  Bump type:        ${BLUE}$BUMP_TYPE${NC}"
echo ""

# Git commit (if not --no-commit)
if [[ "$NO_COMMIT" == false ]]; then
    echo -e "${YELLOW}Creating git commit...${NC}"
    cd "$PROJECT_ROOT"
    git add VERSION frontend/package.json docs/CHANGELOG.md
    git commit -m "chore: bump version to $NEW_VERSION

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
    echo -e "${GREEN}✓ Git commit created${NC}"

    echo ""
    echo -e "To release this version:"
    echo -e "  ${BLUE}git tag -a v$NEW_VERSION -m \"Release v$NEW_VERSION\"${NC}"
    echo -e "  ${BLUE}git push origin main --tags${NC}"
else
    echo -e "${YELLOW}Skipping git commit (--no-commit flag)${NC}"
    echo ""
    echo -e "Files modified:"
    echo -e "  - VERSION"
    echo -e "  - frontend/package.json"
    echo -e "  - docs/CHANGELOG.md"
fi
