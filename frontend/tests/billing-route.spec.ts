import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const billingPagePath = path.resolve(
  process.cwd(),
  "src/routes/(app)/settings/billing/+page.svelte",
);

describe("settings billing page route", () => {
  it("creates the billing page route file", () => {
    expect(existsSync(billingPagePath)).toBe(true);
  });

  it("loads usage data and renders tier and usage meters", () => {
    const page = readFileSync(billingPagePath, "utf-8");

    expect(page).toContain("/api/v1/billing/usage");
    expect(page).toContain("credentials: 'include'");
    expect(page).toContain("Current Tier");
    expect(page).toContain("Agents");
    expect(page).toContain("Conversations");
  });

  it("integrates stripe checkout and stripe customer portal actions", () => {
    const page = readFileSync(billingPagePath, "utf-8");

    expect(page).toContain("/api/v1/billing/checkout-session");
    expect(page).toContain("/api/v1/billing/portal-session");
    expect(page).toContain("Upgrade");
    expect(page).toContain("Manage Subscription");
    expect(page).toContain("stripe");
  });
});
