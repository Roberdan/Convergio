import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

const privacyPagePath = path.resolve(process.cwd(), 'src/routes/privacy/+page.svelte');
const termsPagePath = path.resolve(process.cwd(), 'src/routes/terms/+page.svelte');
const cookiesPagePath = path.resolve(process.cwd(), 'src/routes/cookies/+page.svelte');

describe('public legal pages', () => {
  it('creates privacy, terms, and cookies route files', () => {
    expect(existsSync(privacyPagePath)).toBe(true);
    expect(existsSync(termsPagePath)).toBe(true);
    expect(existsSync(cookiesPagePath)).toBe(true);
  });

  it('privacy policy includes data collection, GDPR rights, retention, and third-party services', () => {
    const page = readFileSync(privacyPagePath, 'utf-8');

    expect(page).toContain('Privacy Policy');
    expect(page).toContain('Data We Collect');
    expect(page).toContain('GDPR Rights');
    expect(page).toContain('Data Retention');
    expect(page).toContain('Third-Party Services');
  });

  it('terms of service includes acceptable use, billing terms, and IP ownership terms', () => {
    const page = readFileSync(termsPagePath, 'utf-8');

    expect(page).toContain('Terms of Service');
    expect(page).toContain('Acceptable Use');
    expect(page).toContain('Billing Terms');
    expect(page).toContain('Intellectual Property');
  });

  it('cookie policy includes necessary, analytics, and functional consent categories', () => {
    const page = readFileSync(cookiesPagePath, 'utf-8');

    expect(page).toContain('Cookie Policy');
    expect(page).toContain('Necessary Cookies');
    expect(page).toContain('Analytics Cookies');
    expect(page).toContain('Functional Cookies');
  });
});
