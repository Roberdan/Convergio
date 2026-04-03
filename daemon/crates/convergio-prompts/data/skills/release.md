## Activation

Run when the user issues `/release` or `/release {{version?}}`. Optional version argument (semver); if omitted, auto-detect from `package.json`.

## Phases

1. **Collect Context** — gather project name (`basename "$(pwd)"`), current branch, uncommitted file count, and current version from manifest
2. **Launch Agent** — delegate to `app-release-manager` subagent with full release gate prompt including: project name, target version, branch; instruct agent to run all five gate categories (pre-flight, build validation, test execution, security audit, code quality, documentation review)
3. **Review Results** — receive agent report: per-check pass/fail status, auto-fixes applied, blocking issues list, recommended next steps
4. **Apply Auto-Fixes** — if agent applied auto-fixes (lint, remove TODOs/debug prints, strip unused imports, trailing whitespace), re-run affected checks; if issues remain → BLOCK
5. **User Decision** — if APPROVED: confirm version bump type (major/minor/patch), create git tag, update CHANGELOG in Keep-a-Changelog format, offer to create GitHub release; if BLOCKED: list all blocking issues, instruct user to fix then re-run `/release`

## Output

- Release report with APPROVE or BLOCK decision
- Per-check status table (Build Quality, Test Execution, Security Audit, Code Quality, Documentation)
- Version bump applied and new tag created (on approval)
- CHANGELOG entry added (on approval)

## Guardrails

- NEVER approve a release with ANY compiler/lint warning, test failure, security vulnerability, TODO/FIXME, hardcoded secret, debug print, or outdated dep with CVE
- NEVER bump version without explicit user confirmation of bump type (major/minor/patch)
- NEVER skip the `app-release-manager` delegation — do not run release checks inline
- NEVER force-push tags or overwrite an existing version tag
