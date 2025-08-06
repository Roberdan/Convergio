import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:4001/login');
    
    // Wait for page to be fully loaded and auth initialization to complete
    await page.waitForSelector('#username');
    await page.waitForSelector('#password');
    
    // Wait a bit for Svelte reactivity to settle
    await page.waitForTimeout(500);
  });

  test('should display login form', async ({ page }) => {
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should login successfully with roberdan credentials', async ({ page }) => {
    // Fill login form
    await page.locator('#username').fill('roberdan');
    await page.locator('#password').fill('admin123');
    
    // Submit form (button should be enabled after filling both fields)
    await page.locator('button[type="submit"]').click();
    
    // Wait for redirect to dashboard
    await page.waitForURL('**/dashboard');
    
    // Verify we're on dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    
    // Check if user is authenticated (navigation should show user info)
    await expect(page.locator('nav')).toContainText('roberdan');
  });

  test('should login successfully with admin credentials', async ({ page }) => {
    // Fill login form
    await page.locator('#username').fill('admin');
    await page.locator('#password').fill('admin123');
    
    // Submit form (button should be enabled after filling both fields)
    await page.locator('button[type="submit"]').click();
    
    // Wait for redirect to dashboard
    await page.waitForURL('**/dashboard');
    
    // Verify we're on dashboard
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill login form with wrong password
    await page.locator('#username').fill('roberdan');
    await page.locator('#password').fill('wrong-password');
    
    // Submit form (button should be enabled after filling both fields)
    await page.locator('button[type="submit"]').click();
    
    // Should show error message (check for the actual error container in the Svelte component)
    await expect(page.locator('.bg-red-50, .text-red-800')).toBeVisible();
    
    // Should stay on login page
    await expect(page).toHaveURL(/.*login/);
  });

  test('should navigate to agents page after login', async ({ page }) => {
    // Login first
    await page.locator('#username').fill('roberdan');
    await page.locator('#password').fill('admin123');
    
    // Submit form (button should be enabled after filling both fields)
    await page.locator('button[type="submit"]').click();
    
    // Wait for dashboard
    await page.waitForURL('**/dashboard');
    
    // Navigate to agents
    await page.click('a[href="/agents"]');
    
    // Verify we're on agents page
    await expect(page).toHaveURL(/.*agents/);
    await expect(page).toHaveTitle(/.*Agents.*/);
  });
});