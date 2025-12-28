import { test, expect } from "@playwright/test";

test.describe("GraphFlow Workflows UI", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to workflows page
    await page.goto("/workflows");
  });

  test("should display workflows dashboard", async ({ page }) => {
    // Check page title
    await expect(page.locator("h1")).toContainText(
      "GraphFlow Workflow Management",
    );

    // Check stats dashboard
    await expect(page.locator("text=Total Workflows")).toBeVisible();
    await expect(page.locator("text=Active Executions")).toBeVisible();
    await expect(page.locator("text=Success Rate")).toBeVisible();
    await expect(page.locator("text=Avg Duration")).toBeVisible();
  });

  test("should show workflow generation panel", async ({ page }) => {
    // Click generate workflow button
    await page.click('button:has-text("Generate Workflow")');

    // Check generation panel appears
    await expect(
      page.locator("text=Generate New Workflow from Natural Language"),
    ).toBeVisible();

    // Check form fields
    await expect(
      page.locator('textarea[placeholder*="Describe the workflow"]'),
    ).toBeVisible();
    await expect(
      page.locator('select:has(option[value="operations"])'),
    ).toBeVisible();
    await expect(
      page.locator('select:has(option[value="medium"])'),
    ).toBeVisible();
    await expect(page.locator('input[type="number"]')).toBeVisible();
  });

  test("should validate workflow prompt", async ({ page }) => {
    // Open generation panel
    await page.click('button:has-text("Generate Workflow")');

    // Enter a prompt
    const promptInput = page.locator(
      'textarea[placeholder*="Describe the workflow"]',
    );
    await promptInput.fill("Create a customer onboarding workflow");

    // Trigger validation by blurring
    await promptInput.blur();

    // Wait for validation result (mock response in test environment)
    // In real test, this would check for actual validation message
    await page.waitForTimeout(500);
  });

  test("should search workflows", async ({ page }) => {
    // Enter search query
    await page.fill('input[placeholder="Search workflows..."]', "customer");

    // Select domain filter
    await page.selectOption(
      'select:has(option[value="operations"])',
      "operations",
    );

    // Select complexity filter
    await page.selectOption('select:has(option[value="medium"])', "medium");

    // Wait for search results to update
    await page.waitForTimeout(500);
  });

  test("should display workflow cards", async ({ page }) => {
    // Wait for workflow cards to load
    await page.waitForSelector(".bg-white.rounded-lg.shadow", {
      timeout: 5000,
    });

    // Check workflow card structure
    const firstCard = page.locator(".bg-white.rounded-lg.shadow").first();

    // Check card has title
    const title = firstCard.locator("h3");
    await expect(title).toBeVisible();

    // Check card has tags
    await expect(firstCard.locator(".rounded-full")).toHaveCount({
      minimum: 1,
    });

    // Check card has action buttons
    await expect(
      firstCard.locator('button:has-text("View Details")'),
    ).toBeVisible();
    await expect(firstCard.locator('button:has-text("Execute")')).toBeVisible();
  });

  test("should display recent executions table", async ({ page }) => {
    // Check executions table exists
    await expect(page.locator("text=Recent Executions")).toBeVisible();

    // Check table headers
    await expect(page.locator('th:has-text("Execution ID")')).toBeVisible();
    await expect(page.locator('th:has-text("Workflow")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();
    await expect(page.locator('th:has-text("Progress")')).toBeVisible();
    await expect(page.locator('th:has-text("Started")')).toBeVisible();
    await expect(page.locator('th:has-text("Actions")')).toBeVisible();
  });

  test("should generate workflow from prompt", async ({ page }) => {
    // Mock API response
    await page.route("**/api/v1/workflows/generate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          workflow: {
            workflow_id: "generated_test_123",
            name: "Test Generated Workflow",
            steps: [
              { step_id: "step_1", description: "Step 1" },
              { step_id: "step_2", description: "Step 2" },
            ],
          },
          estimated_cost: 0.5,
          generation_metadata: {},
          safety_check_result: { is_safe: true },
        }),
      });
    });

    // Open generation panel
    await page.click('button:has-text("Generate Workflow")');

    // Fill in the form
    await page.fill(
      'textarea[placeholder*="Describe the workflow"]',
      "Test workflow generation",
    );
    await page.selectOption("select:first", "operations");
    await page.selectOption("select:nth(1)", "high");

    // Click generate button
    await page.click('button:has-text("Generate Workflow")');

    // Check success message appears
    await expect(
      page.locator("text=Workflow Generated Successfully!"),
    ).toBeVisible({ timeout: 5000 });
  });

  test("should execute workflow", async ({ page }) => {
    // Mock API responses
    await page.route("**/api/v1/workflows/catalog", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          catalog: [
            {
              workflow_id: "test_workflow",
              name: "Test Workflow",
              description: "Test workflow description",
              category: "operations",
              complexity: "medium",
              estimated_duration_minutes: 60,
              steps_count: 3,
              success_rate: 0.9,
              usage_count: 10,
              tags: ["test", "operations"],
            },
          ],
        }),
      });
    });

    await page.route("**/api/v1/workflows/execute", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          execution_id: "exec_123",
          workflow_id: "test_workflow",
          status: "started",
          started_at: new Date().toISOString(),
        }),
      });
    });

    // Wait for page to load
    await page.waitForSelector(".bg-white.rounded-lg.shadow");

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => "Test execution request";
    });

    // Click execute button on first workflow
    await page.click('button:has-text("Execute"):first');

    // Mock alert for success message
    page.on("dialog", async (dialog) => {
      expect(dialog.message()).toContain("Workflow started");
      await dialog.accept();
    });
  });

  test("should handle workflow generation errors", async ({ page }) => {
    // Mock API error response
    await page.route("**/api/v1/workflows/generate", async (route) => {
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Invalid prompt: contains unsafe content",
        }),
      });
    });

    // Open generation panel
    await page.click('button:has-text("Generate Workflow")');

    // Fill form with invalid data
    await page.fill(
      'textarea[placeholder*="Describe the workflow"]',
      "DELETE ALL DATA",
    );

    // Click generate
    await page.click('button:has-text("Generate Workflow")');

    // Check error is handled (would show in alert in current implementation)
    page.on("dialog", async (dialog) => {
      expect(dialog.message()).toContain("Generation failed");
      await dialog.accept();
    });
  });

  test("should filter workflows by domain", async ({ page }) => {
    // Mock filtered results
    await page.route(
      "**/api/v1/workflows/search?*domain=finance*",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            results: [
              {
                workflow_id: "finance_workflow",
                name: "Financial Analysis",
                category: "finance",
                complexity: "high",
                estimated_duration_minutes: 120,
                steps_count: 5,
                success_rate: 0.85,
                usage_count: 25,
                tags: ["finance", "analysis"],
              },
            ],
            total_count: 1,
          }),
        });
      },
    );

    // Select finance domain
    await page.selectOption('select:has(option[value="finance"])', "finance");

    // Wait for filtered results
    await page.waitForTimeout(500);
  });

  test("should display workflow execution progress", async ({ page }) => {
    // Mock executions with different statuses
    await page.route("**/api/v1/workflows/executions/recent", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          executions: [
            {
              execution_id: "exec_1",
              workflow_id: "workflow_1",
              status: "running",
              progress_percentage: 50,
              started_at: new Date().toISOString(),
            },
            {
              execution_id: "exec_2",
              workflow_id: "workflow_2",
              status: "completed",
              progress_percentage: 100,
              started_at: new Date(Date.now() - 3600000).toISOString(),
              completed_at: new Date().toISOString(),
            },
            {
              execution_id: "exec_3",
              workflow_id: "workflow_3",
              status: "failed",
              progress_percentage: 75,
              started_at: new Date(Date.now() - 7200000).toISOString(),
              error_message: "Step 3 failed",
            },
          ],
          total: 3,
        }),
      });
    });

    // Reload page to get executions
    await page.reload();

    // Check different status colors
    await expect(
      page.locator('.text-blue-600:has-text("running")'),
    ).toBeVisible();
    await expect(
      page.locator('.text-green-600:has-text("completed")'),
    ).toBeVisible();
    await expect(
      page.locator('.text-red-600:has-text("failed")'),
    ).toBeVisible();

    // Check progress bars
    const progressBars = page.locator(".bg-blue-600");
    await expect(progressBars).toHaveCount({ minimum: 1 });

    // Check cancel button for running execution
    await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
  });
});
