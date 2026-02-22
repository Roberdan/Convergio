const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..');

describe('T0-07 lint hardening', () => {
  test('frontend ESLint strict config exists and enforces requested rules', () => {
    const eslintConfigPath = path.join(repoRoot, 'frontend/.eslintrc.cjs');
    expect(fs.existsSync(eslintConfigPath)).toBe(true);

    // eslint-disable-next-line global-require, import/no-dynamic-require
    const eslintConfig = require(eslintConfigPath);
    const tsOverride = eslintConfig.overrides.find((override) =>
      String(override.files).includes('.ts')
    );

    expect(tsOverride).toBeDefined();
    expect(tsOverride.rules['@typescript-eslint/no-explicit-any']).toBe('error');
    expect(tsOverride.rules['@typescript-eslint/no-unused-vars'][0]).toBe('error');
    expect(tsOverride.rules['@typescript-eslint/explicit-function-return-type']).toEqual(
      expect.arrayContaining(['error'])
    );
  });

  test('backend Ruff config includes required rule families and limits', () => {
    const pyprojectPath = path.join(repoRoot, 'backend/pyproject.toml');
    expect(fs.existsSync(pyprojectPath)).toBe(true);

    const text = fs.readFileSync(pyprojectPath, 'utf8');
    expect(text).toMatch(/\[tool\.ruff\]/);
    expect(text).toMatch(/line-length\s*=\s*100/);
    expect(text).toMatch(/target-version\s*=\s*"py311"/);
    expect(text).toMatch(/\[tool\.ruff\.lint\]/);

    ['"E"', '"F"', '"W"', '"I"', '"N"', '"UP"', '"ANN"'].forEach((codeFamily) => {
      expect(text).toContain(codeFamily);
    });
  });
});
