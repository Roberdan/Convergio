const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..');

describe('T0-08 CI/CD workflows', () => {
  test('ci workflow has required frontend/backend jobs and triggers', () => {
    const ciPath = path.join(repoRoot, '.github/workflows/ci.yml');
    expect(fs.existsSync(ciPath)).toBe(true);

    const ci = fs.readFileSync(ciPath, 'utf8');

    expect(ci).toMatch(/push:\s*\n\s*branches:\s*\[\s*master\s*\]/);
    expect(ci).toMatch(/pull_request:\s*\n\s*branches:\s*\[\s*master\s*\]/);

    expect(ci).toMatch(/\n\s*frontend:\s*\n/);
    expect(ci).toMatch(/working-directory:\s*\.\/frontend[\s\S]*npm ci/);
    expect(ci).toMatch(/working-directory:\s*\.\/frontend[\s\S]*npm run lint/);
    expect(ci).toMatch(/working-directory:\s*\.\/frontend[\s\S]*npm run check/);
    expect(ci).toMatch(/working-directory:\s*\.\/frontend[\s\S]*continue-on-error:\s*true[\s\S]*npm test/);
    expect(ci).toMatch(/working-directory:\s*\.\/frontend[\s\S]*npm run build/);
    expect(ci).toMatch(/path:\s*\|\s*[\s\S]*frontend\/node_modules/);

    expect(ci).toMatch(/\n\s*backend:\s*\n/);
    expect(ci).toMatch(/python-version:\s*["']3\.11["']/);
    expect(ci).toMatch(/working-directory:\s*\.\/backend[\s\S]*pip install -r requirements\.txt/);
    expect(ci).toMatch(/working-directory:\s*\.\/backend[\s\S]*ruff check src\//);
    expect(ci).toMatch(/working-directory:\s*\.\/backend[\s\S]*continue-on-error:\s*true[\s\S]*pytest --tb=short/);
    expect(ci).toMatch(/path:\s*~\/\.cache\/pip/);
  });

  test('security workflow runs npm audit and pip-audit weekly', () => {
    const securityPath = path.join(repoRoot, '.github/workflows/security.yml');
    expect(fs.existsSync(securityPath)).toBe(true);

    const security = fs.readFileSync(securityPath, 'utf8');
    expect(security).toMatch(/schedule:\s*\n\s*-\s*cron:\s*["'][^"']+["']/);
    expect(security).toMatch(/npm audit/);
    expect(security).toMatch(/pip-audit/);
  });
});
