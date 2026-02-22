import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

const routesRoot = path.resolve(process.cwd(), 'src/routes/admin');

function readRoute(file: string): string {
  return readFileSync(path.join(routesRoot, file), 'utf-8');
}

describe('admin routes', () => {
  it('creates required admin pages and layout', () => {
    const requiredFiles = [
      '+layout.svelte',
      'users/+page.svelte',
      'audit/+page.svelte',
      'tiers/+page.svelte',
      'agents/+page.svelte'
    ];

    for (const file of requiredFiles) {
      expect(existsSync(path.join(routesRoot, file))).toBe(true);
    }
  });

  it('layout contains sidebar links for all admin sections', () => {
    const layout = readRoute('+layout.svelte');

    expect(layout).toContain("href: '/admin/users'");
    expect(layout).toContain("href: '/admin/audit'");
    expect(layout).toContain("href: '/admin/tiers'");
    expect(layout).toContain("href: '/admin/agents'");
  });

  it('admin pages use credentialed fetch calls', () => {
    const usersPage = readRoute('users/+page.svelte');
    const auditPage = readRoute('audit/+page.svelte');
    const tiersPage = readRoute('tiers/+page.svelte');
    const agentsPage = readRoute('agents/+page.svelte');

    expect(usersPage).toContain("credentials: 'include'");
    expect(auditPage).toContain("credentials: 'include'");
    expect(tiersPage).toContain("credentials: 'include'");
    expect(agentsPage).toContain("credentials: 'include'");
  });
});
