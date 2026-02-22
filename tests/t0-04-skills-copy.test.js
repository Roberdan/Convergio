// t0-04-skills-copy.test.js
// Jest test for T0-04: Ensure at least 6 essential skills files exist in .claude/skills/

const fs = require('fs');
const path = require('path');

describe('T0-04: Essential skills copied', () => {
  const skillsDir = path.join(__dirname, '../.claude/skills');
  it('should have at least 6 essential skills .md files', () => {
    if (!fs.existsSync(skillsDir)) throw new Error('.claude/skills/ directory missing');
    const files = fs.readdirSync(skillsDir).filter(f => f.endsWith('.md'));
    expect(files.length).toBeGreaterThanOrEqual(6);
  });
});
