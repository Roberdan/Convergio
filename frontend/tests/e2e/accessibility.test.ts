import { test, expect } from "@playwright/test";

test.describe("Accessibility Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should have proper page titles", async ({ page }) => {
    await expect(page).toHaveTitle(/Convergio/i);

    // Navigate to agents page and check title
    const agentsLink = page.getByRole("link", { name: /agents/i });
    if ((await agentsLink.count()) > 0) {
      await agentsLink.click();
      await expect(page).toHaveTitle(/agents|Convergio/i);
    }
  });

  test("should have proper heading hierarchy", async ({ page }) => {
    // Should have h1 on page
    const h1 = page.getByRole("heading", { level: 1 });
    await expect(h1).toBeVisible();

    // Check that headings are properly structured
    const headings = page.locator("h1, h2, h3, h4, h5, h6");
    const count = await headings.count();
    expect(count).toBeGreaterThan(0);
  });

  test("should have alt text for images", async ({ page }) => {
    const images = page.locator("img");
    const count = await images.count();

    for (let i = 0; i < count; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute("alt");

      // Alt should exist (can be empty for decorative images)
      expect(alt).not.toBeNull();
    }
  });

  test("should have proper link text", async ({ page }) => {
    const links = page.locator("a");
    const count = await links.count();

    for (let i = 0; i < Math.min(count, 10); i++) {
      // Check first 10 links
      const link = links.nth(i);
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute("aria-label");

      // Links should have descriptive text or aria-label
      expect(text || ariaLabel).toBeTruthy();

      if (text) {
        expect(text.trim().length).toBeGreaterThan(0);
        // Avoid generic link text
        expect(text.toLowerCase()).not.toMatch(
          /^(click here|here|more|read more)$/,
        );
      }
    }
  });

  test("should have form labels", async ({ page }) => {
    const inputs = page.locator("input, textarea, select");
    const count = await inputs.count();

    for (let i = 0; i < count; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute("id");
      const ariaLabel = await input.getAttribute("aria-label");
      const ariaLabelledBy = await input.getAttribute("aria-labelledby");

      if (id) {
        // Should have associated label
        const label = page.locator(`label[for="${id}"]`);
        const hasLabel = (await label.count()) > 0;

        // Should have either label, aria-label, or aria-labelledby
        expect(hasLabel || ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    }
  });

  test("should have keyboard navigation support", async ({ page }) => {
    // Test tab navigation through interactive elements
    await page.keyboard.press("Tab");

    // Should have visible focus indicator
    const focusedElement = page.locator(":focus");
    await expect(focusedElement).toBeVisible();

    // Test a few more tab presses
    for (let i = 0; i < 3; i++) {
      await page.keyboard.press("Tab");
      const focused = page.locator(":focus");
      if ((await focused.count()) > 0) {
        await expect(focused).toBeVisible();
      }
    }
  });

  test("should have proper button elements", async ({ page }) => {
    // Check for clickable elements that should be buttons
    const clickableElements = page.locator('[onclick], [role="button"]');
    const count = await clickableElements.count();

    if (count > 0) {
      for (let i = 0; i < Math.min(count, 5); i++) {
        const element = clickableElements.nth(i);
        const tagName = await element.evaluate((el) =>
          el.tagName.toLowerCase(),
        );
        const role = await element.getAttribute("role");

        // Should be actual button or have button role
        expect(tagName === "button" || role === "button").toBeTruthy();
      }
    }
  });

  test("should have sufficient color contrast", async ({ page }) => {
    // Basic check for text visibility
    const textElements = page
      .locator("p, span, div, h1, h2, h3, h4, h5, h6")
      .filter({ hasText: /\w+/ });
    const count = await textElements.count();

    for (let i = 0; i < Math.min(count, 10); i++) {
      const element = textElements.nth(i);

      // Check if text is visible (basic contrast check)
      await expect(element).toBeVisible();

      // Check for proper styling
      const styles = await element.evaluate((el) => {
        const computed = window.getComputedStyle(el);
        return {
          color: computed.color,
          backgroundColor: computed.backgroundColor,
          fontSize: computed.fontSize,
        };
      });

      // Font size should be reasonable
      const fontSize = parseFloat(styles.fontSize);
      expect(fontSize).toBeGreaterThan(10); // At least 11px
    }
  });

  test("should not rely solely on color for information", async ({ page }) => {
    // Look for status indicators, error messages, etc.
    const statusElements = page.locator(
      '[class*="error"], [class*="success"], [class*="warning"], [class*="status"]',
    );
    const count = await statusElements.count();

    if (count > 0) {
      for (let i = 0; i < Math.min(count, 3); i++) {
        const element = statusElements.nth(i);
        const text = await element.textContent();
        const ariaLabel = await element.getAttribute("aria-label");

        // Should have text content or aria-label, not just color
        expect(text?.trim() || ariaLabel).toBeTruthy();
      }
    }
  });

  test("should have proper semantic structure", async ({ page }) => {
    // Check for main landmark
    const main = page.locator('main, [role="main"]');
    if ((await main.count()) > 0) {
      await expect(main).toBeVisible();
    }

    // Check for navigation landmark
    const nav = page.locator('nav, [role="navigation"]');
    if ((await nav.count()) > 0) {
      await expect(nav).toBeVisible();
    }
  });

  test("should handle focus management for dynamic content", async ({
    page,
  }) => {
    // Test focus on dynamic elements (if any)
    const buttons = page
      .locator("button")
      .filter({ hasText: /show|open|menu/i });

    if ((await buttons.count()) > 0) {
      const button = buttons.first();
      await button.click();

      // After interaction, focus should be managed appropriately
      const focusedElement = page.locator(":focus");
      if ((await focusedElement.count()) > 0) {
        await expect(focusedElement).toBeVisible();
      }
    }
  });
});
