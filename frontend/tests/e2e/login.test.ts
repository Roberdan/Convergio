import { test, expect, type Page } from '@playwright/test';

// --- Test Configuration & Best Practices ---
// 1. baseURL: Set a `baseURL` in `playwright.config.ts` to avoid hardcoding URLs.
//    Example: `use: { baseURL: 'http://localhost:4000' }`
// 2. Environment Variables: Store test credentials securely.
//    Create a `.env` file at the root of the `frontend` directory:
//    TEST_USER_USERNAME=roberdan
//    TEST_USER_PASSWORD=your_test_password
//    TEST_ADMIN_USERNAME=admin
//    TEST_ADMIN_PASSWORD=your_admin_password
//    Ensure `.env` is in your `.gitignore` file.
// 3. Robust Selectors: Use `data-testid` attributes in your Svelte components
//    for resilient selectors, e.g., `<div data-testid="error-message">...</div>`.

const TEST_USER = process.env.TEST_USER_USERNAME || 'roberdan';
const TEST_PASS = process.env.TEST_USER_PASSWORD || 'admin123'; // Fallback for local testing
const INVALID_PASS = 'wrong-password';

/**
 * Reusable login function to keep tests DRY.
 * @param page The Playwright page object.
 * @param username The username to use for login.
 * @param password The password to use for login.
 */
async function login(page: Page, username: string, password: string) {
  await page.locator('#username').fill(username);
  await page.locator('#password').fill(password);
  await page.locator('button[type="submit"]').click();
}

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the login page using the baseURL from playwright.config.ts
    await page.goto('/login');

    // Wait for the form to be ready. Playwright's auto-waiting is usually
    // sufficient, so explicit waits like waitForTimeout are not needed.
    await expect(page.locator('#username')).toBeVisible();
  });

  test('should display login form elements', async ({ page }) => {
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should login successfully and redirect to dashboard', async ({ page }) => {
    await login(page, TEST_USER, TEST_PASS);

    // Wait for navigation and verify the URL
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveURL(/.*dashboard/);

    // Check for a welcome message or user identifier in the UI
    await expect(page.locator('nav')).toContainText(TEST_USER);
  });

  test('should show an error message for invalid credentials', async ({ page }) => {
    await login(page, TEST_USER, INVALID_PASS);

    // Use a robust selector like a data-testid for the error message
    // Example: await expect(page.getByTestId('error-message')).toBeVisible();
    const errorMessage = page.locator('.bg-red-50, .text-red-800'); // Kept for now, but should be replaced
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText(/invalid/i); // Check for error text

    // Ensure the page URL has not changed
    await expect(page).toHaveURL(/.*login/);
  });

  test('should allow navigation to other pages after login', async ({ page }) => {
    await login(page, TEST_USER, TEST_PASS);
    await page.waitForURL('**/dashboard');

    // Navigate to the agents page
    await page.getByRole('link', { name: 'Agents' }).click();

    // Verify the new page
    await expect(page).toHaveURL(/.*agents/);
    await expect(page).toHaveTitle(/.*Agents.*/);
  });
});