import { test, expect } from "@playwright/test";

test.describe("Basic Frontend Tests", () => {
  test("homepage loads successfully", async ({ page }) => {
    await page.goto("http://localhost:4000/");

    // Check that the page has loaded
    await expect(page).toHaveTitle(/Convergio/);

    // Check for main heading
    const heading = page.locator("h1");
    await expect(heading).toContainText("Convergio.io");

    // Check for the manifesto section
    const manifesto = page.locator("text=The Agentic Manifesto");
    await expect(manifesto).toBeVisible();
  });

  test("dashboard navigation works", async ({ page }) => {
    await page.goto("http://localhost:4000/");

    // Click on dashboard button
    await page.click("text=Start Your Command Center");

    // Should navigate to dashboard
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test("agents page loads", async ({ page }) => {
    await page.goto("http://localhost:4000/agents");

    // Wait for the page to load
    await page.waitForLoadState("networkidle");

    // Check that we're on the agents page
    await expect(page).toHaveURL(/.*agents/);
  });

  test("backend health check is working", async ({ page }) => {
    const response = await page.request.get("http://localhost:9000/health/");
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty("status");
  });
});
