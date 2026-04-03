## Activation

Run when the user issues `/prepare`, `--check`, `--force`, or `--minimal` flags, or asks to bootstrap/register the current project.

Optional argument: `{{flag?}}` — one of `--check` (verify only), `--force` (overwrite), `--minimal` (30-line CLAUDE.md).

## Phases

1. **Detect Stack** — check for presence of `package.json` (Node.js), `Cargo.toml` (Rust), `go.mod` (Go), `pyproject.toml` (Python); detect commands (build, test, lint) from the manifest
2. **Analyze Structure** — identify key directories (`src/`, `lib/`, `components/`) and project name from `basename "$(pwd)"`
3. **Detect Icon** — search in order: `public/logo*.png`, `assets/icon*.png`, `.claude/icon.png`, `favicon.*`; propose `icon:` field to user for confirmation if found
4. **Generate CLAUDE.md** — create or update `CLAUDE.md` with: project description, `icon:` path (if confirmed), `## Commands` from manifest, `## Architecture` with stack and key paths, `## Project Rules` with verification commands; skip if `--check`
5. **Generate .claudeignore** — create `.claudeignore` with stack-appropriate ignores: Node (`node_modules/`, `dist/`, `.next/`, `coverage/`), Python (`__pycache__/`, `.venv/`, `.pytest_cache/`), General (`.git/`, `.DS_Store`, `*.min.js`)
6. **Register** — add project to `~/.claude/plans/registry.json` with path and icon; skip if `--check`

## Output

- Confirmation of detected stack and commands
- Path of generated/updated `CLAUDE.md`
- Icon path detected (awaiting user confirmation) or "no icon detected"
- Registration status in registry

## Guardrails

- NEVER overwrite existing `CLAUDE.md` without `--force` flag or user confirmation
- NEVER register a project that is already registered without user confirmation
- NEVER emit more than one icon suggestion — search order determines priority
- NEVER skip `.claudeignore` generation for supported stacks
