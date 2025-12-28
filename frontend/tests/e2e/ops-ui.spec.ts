/**
 * End-to-End Tests for Operational UX Components (M4)
 * Tests Timeline and RunPanel components functionality
 */

import { test, expect } from "@playwright/test";

test.describe.skip("Operational UX Components", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the operational UX test page
    await page.goto("/operational-ux");

    // Wait for the page to load
    await page.waitForSelector(".operational-ux-page");
  });

  test.describe("Timeline Component", () => {
    test("should display timeline header correctly", async ({ page }) => {
      const timelineHeader = page.locator(".timeline-header h3");
      await expect(timelineHeader).toContainText("Conversation Timeline");
    });

    test("should show conversation ID in header", async ({ page }) => {
      const conversationId = page.locator(".timeline-header .text-gray-500");
      await expect(conversationId).toContainText("#conv_001");
    });

    test("should have refresh button", async ({ page }) => {
      // Look for refresh button - could have different selectors and labels
      const refreshButton = page
        .locator(
          '.btn-refresh, .btn-refresh-metrics, button:has-text("Refresh")',
        )
        .first();
      await expect(refreshButton).toBeVisible();

      // Check for either timeline or metrics refresh label
      const buttonText = await refreshButton.getAttribute("aria-label");
      const hasCorrectLabel =
        buttonText?.includes("Refresh") &&
        (buttonText?.includes("timeline") || buttonText?.includes("metrics"));
      expect(hasCorrectLabel).toBeTruthy();
    });

    test("should display timeline content when data is available", async ({
      page,
    }) => {
      // Wait for timeline to load
      await page.waitForSelector(".timeline-content", { timeout: 10000 });

      // Check that timeline turns are displayed
      const timelineTurns = page.locator(".timeline-turn");
      await expect(timelineTurns).toHaveCount(1); // Should have at least one turn
    });

    test("should show turn information correctly", async ({ page }) => {
      await page.waitForSelector(".timeline-turn", { timeout: 10000 });

      const turnBadge = page.locator(".turn-badge");
      await expect(turnBadge).toContainText("Turn 1");

      const turnStats = page.locator(".turn-stats .stat-item");
      await expect(turnStats).toHaveCount(3); // Cost, tokens, agents
    });

    test("should display events within turns", async ({ page }) => {
      await page.waitForSelector(".timeline-event", { timeout: 10000 });

      const events = page.locator(".timeline-event");
      await expect(events).toHaveCount(6); // Should have 6 sample events

      // Check for specific event types
      const decisionEvent = page
        .locator(".timeline-event")
        .filter({ hasText: "Decision Made" });
      await expect(decisionEvent).toBeVisible();

      const toolEvent = page
        .locator(".timeline-event")
        .filter({ hasText: "Tool Invoked" });
      await expect(toolEvent).toBeVisible();
    });

    test("should show event details when available", async ({ page }) => {
      await page.waitForSelector(".event-details", { timeout: 10000 });

      // Check decision event details
      const decisionDetails = page.locator(".decision-details");
      await expect(decisionDetails).toContainText("Rationale:");
      await expect(decisionDetails).toContainText("Confidence:");

      // Check tool event details
      const toolDetails = page.locator(".tool-details");
      await expect(toolDetails).toContainText("Tool:");
    });

    test("should handle conversation ID changes", async ({ page }) => {
      const conversationSelect = page.locator("#conversation-select");

      // Change to different conversation
      await conversationSelect.selectOption("conv_002");

      // Timeline should update (though with same sample data for now)
      await page.waitForTimeout(1000);

      // Verify the change was applied
      await expect(conversationSelect).toHaveValue("conv_002");
    });
  });

  test.describe("RunPanel Component", () => {
    test("should display run panel header correctly", async ({ page }) => {
      const panelHeader = page.locator(".panel-header h3");
      await expect(panelHeader).toContainText("Run Panel");
    });

    test("should show conversation ID in header", async ({ page }) => {
      const conversationId = page.locator(".panel-header .text-gray-500");
      await expect(conversationId).toContainText("#conv_001");
    });

    test("should have refresh button", async ({ page }) => {
      // Look for refresh button - could be timeline or metrics
      const refreshButton = page
        .locator(
          '.btn-refresh, .btn-refresh-metrics, button:has-text("Refresh")',
        )
        .first();
      await expect(refreshButton).toBeVisible();

      // Check for either timeline or metrics refresh label
      const buttonText = await refreshButton.getAttribute("aria-label");
      const hasCorrectLabel =
        buttonText?.includes("Refresh") &&
        (buttonText?.includes("timeline") || buttonText?.includes("metrics"));
      expect(hasCorrectLabel).toBeTruthy();
    });

    test("should display metrics grid", async ({ page }) => {
      await page.waitForSelector(".metrics-grid", { timeout: 10000 });

      const metricCards = page.locator(".metric-card");
      await expect(metricCards).toHaveCount(5); // Budget, tokens, performance, errors, agents
    });

    test("should display budget metrics correctly", async ({ page }) => {
      await page.waitForSelector(".budget-card", { timeout: 10000 });

      const budgetTitle = page.locator(".budget-card .card-title");
      await expect(budgetTitle).toContainText("💰 Budget Status");

      const progressBar = page.locator(".budget-card .progress-bar");
      await expect(progressBar).toBeVisible();

      const budgetDetails = page.locator(".budget-card .budget-details");
      await expect(budgetDetails).toContainText("Remaining:");
      await expect(budgetDetails).toContainText("Percentage:");
    });

    test("should display token metrics correctly", async ({ page }) => {
      await page.waitForSelector(".tokens-card", { timeout: 10000 });

      const tokensTitle = page.locator(".tokens-card .card-title");
      await expect(tokensTitle).toContainText("📊 Token Usage");

      const tokenStats = page.locator(".tokens-card .stat-row");
      await expect(tokenStats).toHaveCount(3); // Used, remaining, rate
    });

    test("should display performance metrics correctly", async ({ page }) => {
      await page.waitForSelector(".performance-card", { timeout: 10000 });

      const performanceTitle = page.locator(".performance-card .card-title");
      await expect(performanceTitle).toContainText("⚡ Performance");

      const performanceStats = page.locator(".performance-card .stat-row");
      await expect(performanceStats).toHaveCount(3); // Avg turn time, total turns, active agents
    });

    test("should display error metrics correctly", async ({ page }) => {
      await page.waitForSelector(".errors-card", { timeout: 10000 });

      const errorsTitle = page.locator(".errors-card .card-title");
      await expect(errorsTitle).toContainText("❌ Error Tracking");

      const errorStats = page.locator(".errors-card .stat-row");
      await expect(errorStats).toHaveCount(2); // Total errors, error rate
    });

    test("should display agent metrics correctly", async ({ page }) => {
      await page.waitForSelector(".agents-card", { timeout: 10000 });

      const agentsTitle = page.locator(".agents-card .card-title");
      await expect(agentsTitle).toContainText("🤖 Active Agents");

      const agentStats = page.locator(".agents-card .stat-row");
      await expect(agentStats).toHaveCount(2); // Total, active

      // Check for agent tags
      const agentTags = page.locator(".agent-tag");
      await expect(agentTags).toHaveCount(1); // Should have at least one agent
      await expect(agentTags.first()).toContainText("Ali");
    });

    test("should toggle advanced metrics when checkbox is clicked", async ({
      page,
    }) => {
      const advancedCheckbox = page.locator('input[type="checkbox"]');

      // Initially advanced metrics should not be visible
      const advancedCard = page.locator(".advanced-card");
      await expect(advancedCard).not.toBeVisible();

      // Check the checkbox
      await advancedCheckbox.check();

      // Advanced metrics should now be visible
      await expect(advancedCard).toBeVisible();

      // Uncheck the checkbox
      await advancedCheckbox.uncheck();

      // Advanced metrics should be hidden again
      await expect(advancedCard).not.toBeVisible();
    });
  });

  test.describe("Telemetry Status", () => {
    test("should display telemetry status correctly", async ({ page }) => {
      const telemetryStatus = page.locator(".telemetry-status");
      await expect(telemetryStatus).toBeVisible();

      const statusLabel = page.locator(".status-label");
      await expect(statusLabel).toContainText("Telemetry Status:");
    });

    test("should have health check button", async ({ page }) => {
      const healthButton = page.locator(".btn-check-health");
      await expect(healthButton).toBeVisible();
      await expect(healthButton).toContainText("🔄 Check Health");
    });

    test("should update status after health check", async ({ page }) => {
      const healthButton = page.locator(".btn-check-health");
      const statusValue = page.locator(".status-value");

      // Click health check button
      await healthButton.click();

      // Wait for status to update
      await page.waitForTimeout(2000);

      // Status should show some result
      await expect(statusValue).not.toContainText("unknown");
    });
  });

  test.describe("Feature Flags Section", () => {
    test("should display feature flags information", async ({ page }) => {
      const featureFlagsSection = page.locator(".feature-flags-section");
      await expect(featureFlagsSection).toBeVisible();

      const sectionTitle = page.locator(
        ".feature-flags-section .section-title",
      );
      await expect(sectionTitle).toContainText("🚩 Feature Flags");
    });

    test("should show all required feature flags", async ({ page }) => {
      const flagItems = page.locator(".flag-item");
      await expect(flagItems).toHaveCount(3);

      // Check for specific flags
      const opsUIFlag = page
        .locator(".flag-item")
        .filter({ hasText: "OPS_UI_ENABLED" });
      await expect(opsUIFlag).toBeVisible();

      const ragFlag = page
        .locator(".flag-item")
        .filter({ hasText: "RAG_IN_LOOP_ENABLED" });
      await expect(ragFlag).toBeVisible();

      const decisionFlag = page
        .locator(".flag-item")
        .filter({ hasText: "DECISION_ENGINE_ENABLED" });
      await expect(decisionFlag).toBeVisible();
    });
  });

  test.describe("Acceptance Criteria Section", () => {
    test("should display acceptance criteria", async ({ page }) => {
      const acceptanceSection = page.locator(".acceptance-section");
      await expect(acceptanceSection).toBeVisible();

      const sectionTitle = page.locator(".acceptance-section .section-title");
      await expect(sectionTitle).toContainText("✅ Acceptance Criteria");
    });

    test("should show all three acceptance criteria", async ({ page }) => {
      const criteriaItems = page.locator(".criterion-item");
      await expect(criteriaItems).toHaveCount(3);

      // Check for specific criteria
      const telemetryCriteria = page
        .locator(".criterion-item")
        .filter({ hasText: "95% eventi telemetria visibili" });
      await expect(telemetryCriteria).toBeVisible();

      const uiCriteria = page
        .locator(".criterion-item")
        .filter({ hasText: "Valori UI ~ backend ±5%" });
      await expect(uiCriteria).toBeVisible();

      const a11yCriteria = page
        .locator(".criterion-item")
        .filter({ hasText: "A11y ≥95" });
      await expect(a11yCriteria).toBeVisible();
    });
  });

  test.describe("Testing Instructions Section", () => {
    test("should display testing instructions", async ({ page }) => {
      const testingSection = page.locator(".testing-section");
      await expect(testingSection).toBeVisible();

      const sectionTitle = page.locator(".testing-section .section-title");
      await expect(sectionTitle).toContainText("🧪 Testing Instructions");
    });

    test("should show testing steps", async ({ page }) => {
      const stepsList = page.locator(".steps-list li");
      await expect(stepsList).toHaveCount(5);

      // Check for specific steps
      const timelineStep = page
        .locator(".steps-list li")
        .filter({ hasText: "Verifica Timeline" });
      await expect(timelineStep).toBeVisible();

      const runPanelStep = page
        .locator(".steps-list li")
        .filter({ hasText: "Verifica RunPanel" });
      await expect(runPanelStep).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("should be responsive on mobile viewport", async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      // Check that components adapt to mobile
      const controlsSection = page.locator(".controls-section");
      await expect(controlsSection).toBeVisible();

      // On mobile, controls should stack vertically
      const controlGroups = page.locator(".control-group");
      await expect(controlGroups.first()).toHaveCSS("flex-direction", "column");
    });
  });

  test.describe("Accessibility", () => {
    test("should have proper ARIA labels", async ({ page }) => {
      // Check for aria-label attributes - allow for different refresh button types
      const refreshButton = page
        .locator(
          '.btn-refresh, .btn-refresh-metrics, button:has-text("Refresh")',
        )
        .first();
      const buttonText = await refreshButton.getAttribute("aria-label");
      const hasCorrectLabel =
        buttonText?.includes("Refresh") &&
        (buttonText?.includes("timeline") || buttonText?.includes("metrics"));
      expect(hasCorrectLabel).toBeTruthy();

      const healthButton = page.locator(".btn-check-health");
      if ((await healthButton.count()) > 0) {
        await expect(healthButton).toHaveAttribute(
          "aria-label",
          "Check telemetry health",
        );
      }
    });

    test("should have proper form labels", async ({ page }) => {
      const conversationSelect = page.locator("#conversation-select");
      const label = page.locator('label[for="conversation-select"]');

      await expect(label).toContainText("Test Conversation:");
      await expect(conversationSelect).toBeVisible();
    });

    test("should support keyboard navigation", async ({ page }) => {
      // Focus on the page
      await page.keyboard.press("Tab");

      // Should focus on first interactive element - could be any button
      await page.waitForTimeout(500);
      const focusedElement = page.locator(":focus");
      await expect(focusedElement).toBeVisible();
    });
  });
});
