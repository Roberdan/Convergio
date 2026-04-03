# /interview Skill

Deep Interview mode for iterative requirements extraction.

Asks ONE question at a time (max 7), builds understanding incrementally,
then generates F-xx requirements in the same JSON format as `/prompt`.

## When to use

- Vague or broad user requests that need sharpening
- Greenfield ideas without clear boundaries
- Before `/planner` when requirements are unclear
- When `/prompt` single-round clarification is insufficient

## Invocation

```
/interview
```

Then describe what you want to build. The interview loop starts automatically.

## Output

`.copilot-tracking/prompt-{NNN}.json` — same schema as `/prompt`.
Offers handoff to `/planner` when requirements are confirmed.
