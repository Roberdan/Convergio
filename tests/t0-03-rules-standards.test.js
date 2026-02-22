const fs = require('node:fs');
const path = require('node:path');

const repoRoot = path.resolve(__dirname, '..');

function readText(relPath) {
  return fs.readFileSync(path.join(repoRoot, relPath), 'utf8');
}

describe('T0-03 project-specific .claude/rules standards', () => {
  const ruleFiles = [
    {
      file: '.claude/rules/security-requirements.md',
      requiredSnippets: [
        'input validation',
        'parameterized queries',
        'SQLAlchemy bind params',
        'CORS',
        'CSRF',
        'CSP',
        'HMAC-SHA256',
        'rate limiting mandatory on all public endpoints',
        'no secrets in code',
        '.env'
      ]
    },
    {
      file: '.claude/rules/testing-standards.md',
      requiredSnippets: [
        '80% business logic',
        '100% auth/billing',
        'Vitest for frontend',
        'pytest for backend',
        'isolated tests',
        'no shared state',
        'AAA pattern'
      ]
    },
    {
      file: '.claude/rules/api-standards.md',
      requiredSnippets: [
        'REST',
        '/api/v1/',
        'plural nouns',
        'Pydantic v2 schemas',
        'OpenAPI auto-docs',
        'paginate all lists',
        '4xx/5xx structured errors'
      ]
    },
    {
      file: '.claude/rules/frontend-standards.md',
      requiredSnippets: [
        'Svelte 5 runes only',
        'NO export let',
        'NO $:',
        'NO on:click',
        'Tailwind only',
        'no inline styles',
        'components <250 lines',
        'colocated tests'
      ]
    }
  ];

  test('all rule files exist', () => {
    ruleFiles.forEach(({ file }) => {
      expect(fs.existsSync(path.join(repoRoot, file))).toBe(true);
    });
  });

  test('rule files contain required standards content', () => {
    ruleFiles.forEach(({ file, requiredSnippets }) => {
      const content = readText(file);
      requiredSnippets.forEach((snippet) => {
        expect(content).toContain(snippet);
      });
    });
  });
});
