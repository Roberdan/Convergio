const fs = require('fs');
const path = require('path');

describe('CHANGELOG.md W0 update', () => {
  const changelogPath = path.resolve(__dirname, '../CHANGELOG.md');

  it('should mention v4.0.0', () => {
    const content = fs.readFileSync(changelogPath, 'utf8');
    expect(content).toMatch(/v4\.0\.0/);
  });

  it('should mention hardening or CI', () => {
    const content = fs.readFileSync(changelogPath, 'utf8');
    expect(content).toMatch(/hardening|CI/i);
  });
});
