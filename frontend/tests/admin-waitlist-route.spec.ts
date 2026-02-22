import { describe, it, expect } from 'vitest';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

const adminRoot = path.resolve(process.cwd(), 'src/routes/admin');
const waitlistPagePath = path.join(adminRoot, 'waitlist/+page.svelte');
const adminLayoutPath = path.join(adminRoot, '+layout.svelte');

describe('admin waitlist route', () => {
  it('creates the waitlist admin page route file', () => {
    expect(existsSync(waitlistPagePath)).toBe(true);
  });

  it('adds waitlist link to admin sidebar navigation', () => {
    const layout = readFileSync(adminLayoutPath, 'utf-8');

    expect(layout).toContain("href: '/admin/waitlist'");
    expect(layout).toContain("label: 'Waitlist'");
  });

  it('renders pending requests table with approve and reject actions', () => {
    const page = readFileSync(waitlistPagePath, 'utf-8');

    expect(page).toContain('Pending Waitlist Requests');
    expect(page).toContain('Approve');
    expect(page).toContain('Reject');
  });

  it('calls admin waitlist APIs with credentialed fetch and supports email preview', () => {
    const page = readFileSync(waitlistPagePath, 'utf-8');

    expect(page).toContain('/api/v1/admin/waitlist');
    expect(page).toContain('/approve');
    expect(page).toContain('/reject');
    expect(page).toContain("credentials: 'include'");
    expect(page).toContain('Email Preview');
    expect(page).toContain('Preview invite email before sending');
  });
});
