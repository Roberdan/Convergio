const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..');
const claudeConfigPath = path.join(repoRoot, '.claude', 'CLAUDE.md');

function readConfig() {
  return fs.readFileSync(claudeConfigPath, 'utf8');
}

describe('T0-02 CLAUDE project configuration', () => {
  test('contains required gate and rules sections', () => {
    const content = readConfig();
    expect(content).toContain('Thor Gate');
    expect(content).toContain('Anti-Bypass');
    expect(content).toContain('Core Rules');
  });

  test('contains frontend runes and backend linting conventions', () => {
    const content = readConfig();
    expect(content).toMatch(/runes|\$state|\$derived/);
    expect(content).toContain('ruff');
  });
});
