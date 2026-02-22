const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..');

function readText(relPath) {
  return fs.readFileSync(path.join(repoRoot, relPath), 'utf8');
}

describe('T0-01 repository hardening', () => {
  test('required hardening files exist', () => {
    const required = [
      '.husky/pre-commit',
      '.husky/pre-push',
      '.husky/commit-msg',
      'scripts/secret-scan.sh',
      '.editorconfig'
    ];

    required.forEach((filePath) => {
      expect(fs.existsSync(path.join(repoRoot, filePath))).toBe(true);
    });
  });

  test('husky hooks contain required commands', () => {
    const preCommit = readText('.husky/pre-commit');
    const prePush = readText('.husky/pre-push');
    const commitMsg = readText('.husky/commit-msg');

    expect(preCommit).toContain('cd frontend && npx lint-staged');
    expect(preCommit).toContain('cd ../backend && ruff check src/');

    expect(prePush).toContain('cd frontend && npm run check && npm test');
    expect(prePush).toContain('cd ../backend && pytest --tb=short -q');

    expect(commitMsg).toMatch(/conventional|feat|fix|docs|chore|refactor|test/);
  });

  test('frontend lint-staged config includes svelte and ts formatting/linting', () => {
    const frontendPkg = JSON.parse(readText('frontend/package.json'));

    expect(frontendPkg['lint-staged']).toBeDefined();
    expect(frontendPkg['lint-staged']['*.svelte']).toEqual(expect.arrayContaining(['eslint --fix', 'prettier --write']));
    expect(frontendPkg['lint-staged']['*.ts']).toEqual(expect.arrayContaining(['eslint --fix', 'prettier --write']));
  });

  test('secret scanner script checks staged files for secrets', () => {
    const script = readText('scripts/secret-scan.sh');

    expect(script).toContain('git diff --cached --name-only');
    expect(script).toMatch(/api[_-]?key/i);
    expect(script).toMatch(/password/i);
    expect(script).toMatch(/token/i);
  });

  test('gitignore and editorconfig are hardened', () => {
    const gitignore = readText('.gitignore');
    const editorconfig = readText('.editorconfig');

    expect(gitignore).toContain('prisma/');
    expect(gitignore).toContain('grafana/');
    expect(gitignore).toContain('.env.production*');
    expect(gitignore).toContain('node_modules/');

    expect(editorconfig).toContain('root = true');
    expect(editorconfig).toContain('indent_style =');
    expect(editorconfig).toContain('end_of_line =');
  });
});
