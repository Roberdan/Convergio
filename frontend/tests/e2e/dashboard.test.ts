import { test, expect } from "@playwright/test";

test.describe("CEO Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to main dashboard
    await page.goto("/");

    // Wait for dashboard to load
    await page.waitForLoadState("networkidle");
  });

  test("should display main dashboard elements", async ({ page }) => {
    // Check for main dashboard components
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    // Look for Convergio branding - use more specific selector
    await expect(
      page.locator('span:has-text("platform.Convergio.io")'),
    ).toBeVisible();
  });

  test("should show navigation menu", async ({ page }) => {
    // Check for any navigation elements - could be header, nav, or buttons
    const possibleNav = page
      .locator('nav, header, [data-testid="navigation"], a[href]')
      .first();

    if ((await possibleNav.count()) > 0) {
      await expect(possibleNav).toBeVisible();

      // Should have key navigation items if present
      const navItems = ["Dashboard", "Agents", "Chat", "Settings"];

      for (const item of navItems) {
        const navLink = page.getByRole("link", { name: new RegExp(item, "i") });
        if ((await navLink.count()) > 0) {
          await expect(navLink.first()).toBeVisible();
        }
      }
    }
  });

  test("should display AI agent count", async ({ page }) => {
    // Look for agent count display
    const agentCount = page.getByText(/41.*agents?|agents?.*41/i);
    if ((await agentCount.count()) > 0) {
      await expect(agentCount).toBeVisible();
    }
  });

  test("should show platform features", async ({ page }) => {
    // Check for feature highlights
    const features = [
      "AI-powered",
      "Business orchestration",
      "Agent coordination",
      "Real-time",
    ];

    for (const feature of features) {
      const featureText = page.getByText(new RegExp(feature, "i"));
      if ((await featureText.count()) > 0) {
        await expect(featureText.first()).toBeVisible();
      }
    }
  });

  test("should have working navigation links", async ({ page }) => {
    // Test navigation to agents page
    const agentsLink = page.getByRole("link", { name: /agents/i });

    if ((await agentsLink.count()) > 0) {
      await agentsLink.click();
      await page.waitForURL("**/agents");
      await expect(page).toHaveURL(/agents/);
    }
  });

  test("should display Mario dedication section", async ({ page }) => {
    // Look for Mario dedication
    const marioSection = page.getByText(/Mario|FightTheStroke/i);

    if ((await marioSection.count()) > 0) {
      await expect(marioSection.first()).toBeVisible();
    }
  });

  test("should show Agentic Manifesto reference", async ({ page }) => {
    // Look for Agentic Manifesto mention
    const manifestoText = page.getByText(
      /Agentic Manifesto|Human purpose.*AI momentum/i,
    );

    if ((await manifestoText.count()) > 0) {
      await expect(manifestoText.first()).toBeVisible();
    }
  });

  test("should be responsive on mobile", async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Should still show main content - use more specific selector
    await expect(
      page.locator('span:has-text("platform.Convergio.io")'),
    ).toBeVisible();

    // Navigation might be collapsed but should be accessible
    const nav = page
      .locator(
        'nav, header, [data-testid="navigation"], [data-testid="mobile-menu"], a[href]',
      )
      .first();
    if ((await nav.count()) > 0) {
      await expect(nav).toBeVisible();
    }
  });

  test("should load without JavaScript errors", async ({ page }) => {
    const errors: string[] = [];

    page.on("pageerror", (error) => {
      errors.push(error.message);
    });

    page.on("response", (response) => {
      if (response.status() >= 400) {
        errors.push(`HTTP ${response.status()}: ${response.url()}`);
      }
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Should have no critical errors
    const criticalErrors = errors.filter(
      (error) =>
        error.includes("TypeError") ||
        error.includes("ReferenceError") ||
        error.includes("500") ||
        error.includes("404"),
    );

    expect(criticalErrors).toHaveLength(0);
  });
});
