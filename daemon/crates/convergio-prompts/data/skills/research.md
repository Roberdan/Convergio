## Activation

Run when invoked as `/research` or when asked to investigate a topic before planning or implementation. Do NOT write code or make changes.

## Phases

### Phase 1: Convention Discovery

1. Read the project's `CLAUDE.md` and rules directory.
2. Read relevant filetype instructions.
3. Identify applicable coding standards and conventions.

### Phase 2: Codebase Investigation

1. Define research scope and explicit questions to answer.
2. Use Explore agents for discovery.
3. Read key files and trace relevant code paths.
4. Document patterns, APIs, and dependencies found.

### Phase 3: External Research (if needed)

1. Search documentation, APIs, and library references.
2. Verify version compatibility.
3. Note breaking changes or deprecations.

### Phase 4: Alternatives Analysis

1. Identify 2–3 viable approaches.
2. Compare trade-offs: complexity, performance, maintainability.
3. Select ONE recommended approach with rationale.
4. Document why alternatives were rejected.

### Phase 5: Output

Save research document to: `.copilot-tracking/research/{{date}}-{{description}}-research.md`

Document structure:

```
# Research: {Task Description}

Date: {YYYY-MM-DD}

## Scope
- Goal: [one sentence]
- Questions: [bulleted list]
- Assumptions: [bulleted list]

## Codebase Analysis
- Files examined: [paths with line references]
- Patterns found: [conventions, architecture]
- Dependencies: [libraries/versions]

## Key Discoveries
[Numbered findings with evidence. Include file:line references]

## Recommended Approach
**Selected**: [approach name]
**Rationale**: [why this over alternatives]
**Implementation sketch**: [high-level steps, NOT code]

## Alternatives Considered
| Approach | Pros | Cons | Rejected Because |

## Open Questions
[Anything needing user clarification before planning]
```

End output with: "Research complete. Proceed with `/planner`?"

## Output

- Single authoritative research document at the path above.
- All findings cited with file:line or URL references.

## Guardrails

- NEVER write implementation code — only analysis and recommendations.
- NEVER leave findings uncited — every claim needs a source (file:line, URL, or doc reference).
- NEVER skip saving output as a file — in-context only is not acceptable.
- NEVER proceed to implementation — hand off to `/planner` explicitly.
