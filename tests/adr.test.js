// jest test for ADRs and plan notes
const fs = require('fs');
const path = require('path');

describe('ADR and Plan Notes Verification', () => {
  const adrDir = path.join(__dirname, '../docs/adr');
  const adrFiles = [
    'ADR-001-MIGRATION-TO-AGENT-FRAMEWORK.md',
    'ADR-002-AGENT-FRAMEWORK-1.0-UPGRADE.md',
    'ADR-003-SESSION-AUTH-HMAC.md',
    'ADR-004-PRISMA-SQLALCHEMY-DUAL-ORM.md',
    'ADR-005-SVELTE5-MIGRATION.md',
  ];
  const notesFile = path.join(adrDir, 'plan-193-notes.md');

  test('At least 3 ADR files exist', () => {
    const files = fs.readdirSync(adrDir).filter(f => f.endsWith('.md'));
    expect(files.length).toBeGreaterThanOrEqual(3);
  });

  test('ADR-004 and ADR-005 exist', () => {
    adrFiles.slice(3).forEach(f => {
      expect(fs.existsSync(path.join(adrDir, f))).toBe(true);
    });
  });

  test('plan-193-notes.md exists and is not empty', () => {
    expect(fs.existsSync(notesFile)).toBe(true);
    const content = fs.readFileSync(notesFile, 'utf8');
    expect(content.trim().length).toBeGreaterThan(0);
  });
});
