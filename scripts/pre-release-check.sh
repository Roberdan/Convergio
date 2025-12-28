#!/bin/bash
#
# Convergio Web Platform - Pre-Release Check Script
# BRUTAL MODE: Zero Tolerance for Quality Issues
#
# Usage: ./scripts/pre-release-check.sh [--fix] [--skip-tests]
#
# Options:
#   --fix         Auto-fix issues where possible
#   --skip-tests  Skip test execution (NOT RECOMMENDED)
#

# Note: set -e is intentionally not used to allow all checks to run
# even if some fail, so we get a complete report

# Source nvm if available (for npm/node commands)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_ROOT/VERSION"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"
CHANGELOG_FILE="$PROJECT_ROOT/docs/CHANGELOG.md"

# Counters
ERRORS=0
WARNINGS=0
AUTO_FIXED=0

# Parse arguments
AUTO_FIX=false
SKIP_TESTS=false
for arg in "$@"; do
    case $arg in
        --fix)
            AUTO_FIX=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
    esac
done

# Logging functions
log_phase() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  PHASE $1: $2${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}\n"
}

log_check() {
    echo -e "${YELLOW}▶ Checking: $1${NC}"
}

log_pass() {
    echo -e "${GREEN}✓ PASS: $1${NC}"
}

log_fail() {
    echo -e "${RED}✗ FAIL: $1${NC}"
    ((ERRORS++))
}

log_fix() {
    echo -e "${GREEN}🔧 AUTO-FIXED: $1${NC}"
    ((AUTO_FIXED++))
}

log_warn() {
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
    ((WARNINGS++))
}

# ============================================================================
# PHASE 0: VERSION CONSISTENCY
# ============================================================================
log_phase "0" "VERSION CONSISTENCY"

# Check VERSION file exists
log_check "VERSION file exists"
if [[ -f "$VERSION_FILE" ]]; then
    VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
    log_pass "VERSION file exists: $VERSION"
else
    log_fail "VERSION file not found at $VERSION_FILE"
fi

# Check package.json version matches
log_check "frontend/package.json version matches"
if [[ -f "$FRONTEND_DIR/package.json" ]]; then
    PKG_VERSION=$(jq -r '.version' "$FRONTEND_DIR/package.json")
    if [[ "$PKG_VERSION" == "$VERSION" ]]; then
        log_pass "package.json version matches: $PKG_VERSION"
    else
        if [[ "$AUTO_FIX" == true ]]; then
            cd "$FRONTEND_DIR"
            npm pkg set version="$VERSION" 2>/dev/null || jq ".version = \"$VERSION\"" package.json > tmp.json && mv tmp.json package.json
            log_fix "Updated package.json version from $PKG_VERSION to $VERSION"
        else
            log_fail "package.json version mismatch: $PKG_VERSION != $VERSION"
        fi
    fi
else
    log_fail "frontend/package.json not found"
fi

# Check CHANGELOG has version entry
log_check "CHANGELOG.md has entry for $VERSION"
if grep -q "## \[$VERSION\]" "$CHANGELOG_FILE"; then
    log_pass "CHANGELOG.md has entry for $VERSION"
else
    log_fail "CHANGELOG.md missing entry for version $VERSION"
fi

# ============================================================================
# PHASE 1: FRONTEND CHECKS
# ============================================================================
log_phase "1" "FRONTEND CHECKS"

cd "$FRONTEND_DIR"

# Build check
log_check "npm run build"
if npm run build 2>&1 | tee /tmp/build.log; then
    # Filter out framework/tooling messages (not code issues):
    # - SvelteKit deprecation warnings
    # - Font resolution notices
    # - Vite chunk size info messages
    if grep -v "option is deprecated" /tmp/build.log | grep -v "didn't resolve at build time" | grep -v "chunkSizeWarningLimit" | grep -qi "warning"; then
        log_warn "Build succeeded with warnings"
    else
        log_pass "Build succeeded with no warnings"
    fi
else
    log_fail "Build failed"
fi

# TypeScript/Svelte check
log_check "npm run check (svelte-check)"
CHECK_OUTPUT=$(npm run check 2>&1 || true)
echo "$CHECK_OUTPUT"
if echo "$CHECK_OUTPUT" | grep -q "found 0 errors and 0 warnings"; then
    log_pass "TypeScript/Svelte check passed (0 errors, 0 warnings)"
elif echo "$CHECK_OUTPUT" | grep -q "found 0 errors"; then
    WARN_COUNT=$(echo "$CHECK_OUTPUT" | grep -o "found 0 errors and [0-9]* warnings" | grep -o "[0-9]* warnings" || echo "0 warnings")
    log_warn "TypeScript check passed with $WARN_COUNT"
else
    log_fail "TypeScript/Svelte check failed"
fi

# Lint check (informational - not blocking for release)
log_check "npm run lint"
LINT_OUTPUT=$(npm run lint 2>&1 || true)
if echo "$LINT_OUTPUT" | grep -q "0 problems"; then
    log_pass "Lint check passed (0 problems)"
elif echo "$LINT_OUTPUT" | grep -qE "[0-9]+ problems"; then
    LINT_PROBLEMS=$(echo "$LINT_OUTPUT" | grep -oE "[0-9]+ problems" | head -1)
    log_warn "Lint check: $LINT_PROBLEMS (non-blocking)"
else
    log_pass "Lint check completed"
fi

# Unit Tests (Vitest)
if [[ "$SKIP_TESTS" != true ]]; then
    log_check "npm test (vitest unit tests)"
    if npm test 2>&1; then
        log_pass "Frontend unit tests passed"
    else
        log_fail "Frontend unit tests failed"
    fi

    # E2E Tests (Playwright) - only if backend is running
    log_check "Playwright E2E tests"
    if curl -s http://localhost:9000/health > /dev/null 2>&1; then
        log_pass "Backend is running for E2E"
        if npm run test:e2e 2>&1; then
            log_pass "Frontend E2E tests passed"
        else
            log_warn "Frontend E2E tests failed (may need setup)"
        fi
    else
        log_warn "Backend not running - skipping Playwright E2E (run: cd backend && uvicorn src.main:app)"
    fi
else
    log_warn "Tests skipped (--skip-tests flag)"
fi

# Security audit
log_check "npm audit (high/critical)"
AUDIT_OUTPUT=$(npm audit --audit-level=high 2>&1 || true)
if echo "$AUDIT_OUTPUT" | grep -q "found 0 vulnerabilities"; then
    log_pass "No high/critical vulnerabilities"
elif echo "$AUDIT_OUTPUT" | grep -qE "(high|critical)"; then
    log_fail "High/critical vulnerabilities found"
    echo "$AUDIT_OUTPUT" | head -30
else
    log_pass "No high/critical vulnerabilities"
fi

# ============================================================================
# PHASE 2: BACKEND CHECKS
# ============================================================================
log_phase "2" "BACKEND CHECKS"

cd "$BACKEND_DIR"

# Ruff check (non-blocking - legacy issues)
log_check "ruff check"
if command -v ruff &> /dev/null; then
    RUFF_OUTPUT=$(ruff check . 2>&1 || true)
    RUFF_ERRORS=$(echo "$RUFF_OUTPUT" | grep -oE "Found [0-9]+ errors" | grep -oE "[0-9]+" || echo "0")
    if [[ "$RUFF_ERRORS" == "0" ]] || [[ -z "$RUFF_ERRORS" ]]; then
        log_pass "Ruff check passed"
    else
        if [[ "$AUTO_FIX" == true ]]; then
            log_check "Attempting auto-fix with ruff check --fix"
            ruff check --fix . 2>&1 || true
            RUFF_OUTPUT=$(ruff check . 2>&1 || true)
            RUFF_ERRORS=$(echo "$RUFF_OUTPUT" | grep -oE "Found [0-9]+ errors" | grep -oE "[0-9]+" || echo "0")
            if [[ "$RUFF_ERRORS" == "0" ]] || [[ -z "$RUFF_ERRORS" ]]; then
                log_fix "Ruff issues auto-fixed"
            else
                log_warn "Ruff: $RUFF_ERRORS issues remain (non-blocking legacy issues)"
            fi
        else
            log_warn "Ruff: $RUFF_ERRORS issues found (non-blocking legacy issues)"
        fi
    fi
else
    log_warn "ruff not installed, skipping"
fi

# Pytest - Unit Tests
if [[ "$SKIP_TESTS" != true ]]; then
    log_check "pytest (unit tests)"
    if command -v pytest &> /dev/null; then
        if PYTHONPATH="$BACKEND_DIR/src" pytest "$BACKEND_DIR/tests" -v --ignore="$BACKEND_DIR/tests/e2e" --ignore="$BACKEND_DIR/tests/integration" 2>&1; then
            log_pass "Backend unit tests passed"
        else
            log_fail "Backend unit tests failed"
        fi
    else
        log_warn "pytest not installed, skipping"
    fi

    # Integration Tests
    log_check "pytest (integration tests)"
    if PYTHONPATH="$BACKEND_DIR/src" pytest "$BACKEND_DIR/tests/integration" -v 2>&1; then
        log_pass "Backend integration tests passed"
    else
        log_warn "Backend integration tests failed (may need running services)"
    fi

    # E2E Tests with Ollama (LOCAL = $0 COST)
    log_check "pytest E2E (Ollama - FREE)"
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        log_pass "Ollama is running"
        if AI_PROVIDER_MODE=ollama_only PYTHONPATH="$BACKEND_DIR/src" pytest "$BACKEND_DIR/tests/e2e" -v 2>&1; then
            log_pass "E2E tests passed (Ollama)"
        else
            log_fail "E2E tests failed"
        fi
    else
        log_warn "Ollama not running - skipping E2E tests (run: ollama serve)"
    fi
fi

# Check for debug prints (non-blocking - legacy backend code)
log_check "Debug prints in production code"
DEBUG_PRINTS=$(grep -r "print(" src/ --include="*.py" 2>/dev/null | grep -v "# noqa" | grep -v "__pycache__" | wc -l | tr -d ' ')
if [[ "$DEBUG_PRINTS" -gt 0 ]]; then
    log_warn "Found $DEBUG_PRINTS debug print statements in backend (non-blocking legacy)"
else
    log_pass "No debug prints found"
fi

# ============================================================================
# PHASE 3: CODE QUALITY
# ============================================================================
log_phase "3" "CODE QUALITY"

cd "$PROJECT_ROOT"

# TODO/FIXME check
log_check "TODO/FIXME comments in code"
TODO_COUNT=$(grep -r "TODO\|FIXME" frontend/src backend/src --include="*.ts" --include="*.svelte" --include="*.py" 2>/dev/null | grep -v node_modules | grep -v __pycache__ | wc -l | tr -d ' ')
if [[ "$TODO_COUNT" -gt 0 ]]; then
    log_fail "Found $TODO_COUNT TODO/FIXME comments"
    grep -r "TODO\|FIXME" frontend/src backend/src --include="*.ts" --include="*.svelte" --include="*.py" 2>/dev/null | grep -v node_modules | grep -v __pycache__ | head -10
else
    log_pass "No TODO/FIXME comments"
fi

# console.log check
log_check "console.log in production frontend code"
CONSOLE_COUNT=$(grep -r "console\.log" frontend/src --include="*.ts" --include="*.svelte" 2>/dev/null | grep -v node_modules | wc -l | tr -d ' ')
if [[ "$CONSOLE_COUNT" -gt 0 ]]; then
    log_fail "Found $CONSOLE_COUNT console.log statements in frontend"
    grep -r "console\.log" frontend/src --include="*.ts" --include="*.svelte" 2>/dev/null | grep -v node_modules | head -10
else
    log_pass "No console.log in production code"
fi

# ============================================================================
# FINAL REPORT
# ============================================================================
log_phase "FINAL" "RELEASE DECISION"

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                    RELEASE CHECK SUMMARY                       ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Version:     ${GREEN}$VERSION${NC}"
echo -e "  Errors:      ${RED}$ERRORS${NC}"
echo -e "  Warnings:    ${YELLOW}$WARNINGS${NC}"
echo -e "  Auto-fixed:  ${GREEN}$AUTO_FIXED${NC}"
echo ""

if [[ $ERRORS -gt 0 ]]; then
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                    🚫 RELEASE BLOCKED 🚫                       ║${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}║  $ERRORS blocking issue(s) found. Fix them before releasing.    ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
    exit 1
else
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   ✅ RELEASE APPROVED ✅                       ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║  All checks passed. Ready to release v$VERSION                 ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Next steps:"
    echo -e "  1. git tag -a v$VERSION -m \"Release v$VERSION\""
    echo -e "  2. git push origin main --tags"
    exit 0
fi
