import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

const landingPagePath = path.resolve(process.cwd(), 'src/routes/+page.svelte');
const rootLayoutPath = path.resolve(process.cwd(), 'src/routes/+layout.svelte');
const landingComponentPath = path.resolve(
  process.cwd(),
  'src/lib/components/landing/LandingPage.svelte'
);

describe('public landing page route', () => {
  it('creates landing page component and route file', () => {
    expect(existsSync(landingPagePath)).toBe(true);
    expect(existsSync(landingComponentPath)).toBe(true);
  });

  it('renders hero, features, pricing, waitlist and agent showcase sections', () => {
    const page = readFileSync(landingPagePath, 'utf-8');

    expect(page).toContain('Human purpose. AI momentum.');
    expect(page).toContain('hero');
    expect(page).toContain('features');
    expect(page).toContain('pricing');
    expect(page).toContain('waitlist');
    expect(page).toContain('carousel');
  });

  it('uses waitlist API for CTA form submissions', () => {
    const landingComponent = readFileSync(landingComponentPath, 'utf-8');

    expect(landingComponent).toContain('/api/v1/waitlist');
    expect(landingComponent).toContain("method: 'POST'");
  });
});

describe('root layout auth routing', () => {
  it('redirects authenticated users from / to /dashboard', () => {
    const layout = readFileSync(rootLayoutPath, 'utf-8');

    expect(layout).toContain('authStore');
    expect(layout).toContain("$page.url.pathname === '/'");
    expect(layout).toContain("goto('/dashboard')");
  });
});
