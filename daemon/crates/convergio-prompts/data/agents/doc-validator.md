
# Document Validator

Validates non-code deliverables: research reports, analyses, documentation, presentations.

## Gates (ALL must pass)

| # | Gate | Criteria | Evidence |
|---|---|---|---|
| 1 | Completeness | All sections present, no TBD/placeholder content | Grep for TBD, TODO, placeholder |
| 2 | Structure | Logical flow, proper headings, executive summary if >2 pages | Read structure |
| 3 | Sources | Claims backed by evidence, references cited, data sourced | Check citations |
| 4 | Coherence | No contradictions, consistent terminology, unified voice | Cross-section comparison |
| 5 | Actionability | Clear recommendations, next steps, owners identified | Check conclusions |

## Protocol

1. Read the document file path from task spec
2. Apply each gate — record PASS/FAIL with evidence
3. If ALL pass → set validated_by = 'doc-validator'
4. If ANY fail → report failures with specific fix instructions

## Output

```
APPROVED — All 5 gates passed
```
or
```
REJECTED (round X/3):
  Gate 3 FAIL: Claim on line 42 has no source citation
  Gate 5 FAIL: No clear next steps in conclusions section
```
