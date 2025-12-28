/**
 * Agent Interaction Helpers for Playwright E2E Tests
 * Utilities for interacting with Convergio AI agents
 */

import { Page, expect } from "@playwright/test";

export interface AgentResponse {
  agent: string;
  message: string;
  timestamp: Date;
  length: number;
}

/**
 * Wait for AI response with variable timing
 */
export async function waitForAIResponse(
  page: Page,
  selector: string,
  minLength: number = 100,
  timeoutMs: number = 30000,
): Promise<string> {
  // Wait for the response element to appear
  await page.waitForSelector(selector, { timeout: timeoutMs });

  // Wait for content to be substantial (AI responses take time)
  await page.waitForFunction(
    ([sel, len]) => {
      const element = document.querySelector(sel);
      const content = element?.textContent || "";
      return content.length > len && !content.includes("Loading...");
    },
    [selector, minLength],
    { timeout: timeoutMs },
  );

  const content = await page.textContent(selector);
  return content || "";
}

/**
 * Send query to specific agent
 */
export async function sendAgentQuery(
  page: Page,
  agentName: string,
  query: string,
): Promise<void> {
  // Navigate to agent if not already there
  const currentUrl = page.url();
  if (
    !currentUrl.includes(agentName.toLowerCase().replace(/[^a-z0-9]/g, "_"))
  ) {
    await page.goto(
      `/agents/${agentName.toLowerCase().replace(/[^a-z0-9]/g, "_")}`,
    );
  }

  // Wait for chat interface
  await page.waitForSelector('[data-testid="chat-input"]', { timeout: 10000 });

  // Clear and type query
  await page.fill('[data-testid="chat-input"]', "");
  await page.type('[data-testid="chat-input"]', query);

  // Send message
  await page.click('[data-testid="send-button"]');

  // Wait a moment for the message to be processed
  await page.waitForTimeout(1000);
}

/**
 * Send query to Ali (Chief of Staff) - primary interface
 */
export async function sendAliQuery(page: Page, query: string): Promise<void> {
  return sendAgentQuery(page, "ali_chief_of_staff", query);
}

/**
 * Validate AI response quality
 */
export function validateAIQuality(response: string): boolean {
  if (!response || response.length < 50) return false;

  // Check for common fallback/error patterns
  const errorPatterns = [
    "I cannot",
    "I am unable",
    "fallback",
    "error occurred",
    "try again",
    "something went wrong",
  ];

  const lowercaseResponse = response.toLowerCase();
  const hasErrors = errorPatterns.some((pattern) =>
    lowercaseResponse.includes(pattern.toLowerCase()),
  );

  if (hasErrors) return false;

  // Check for substantial content
  const wordCount = response.trim().split(/\s+/).length;
  const hasSubstantialContent = wordCount >= 20;

  // Check for structured thinking (good AI responses often have structure)
  const hasStructure =
    response.includes("\n") ||
    response.includes("•") ||
    response.includes("-") ||
    response.includes("1.") ||
    response.includes("**");

  return hasSubstantialContent && (wordCount > 50 || hasStructure);
}

/**
 * Get agent response from chat interface
 */
export async function getLatestAgentResponse(
  page: Page,
  timeoutMs: number = 30000,
): Promise<AgentResponse> {
  // Wait for response to appear
  const responseSelector =
    '[data-testid="agent-message"]:last-child [data-testid="message-content"]';

  const content = await waitForAIResponse(
    page,
    responseSelector,
    50,
    timeoutMs,
  );

  // Extract agent name from message container
  const agentNameSelector =
    '[data-testid="agent-message"]:last-child [data-testid="agent-name"]';
  const agentName = await page
    .textContent(agentNameSelector)
    .catch(() => "Unknown");

  return {
    agent: agentName || "Unknown",
    message: content,
    timestamp: new Date(),
    length: content.length,
  };
}

/**
 * Wait for multi-agent orchestration to complete
 */
export async function waitForOrchestration(
  page: Page,
  expectedAgents: string[],
  timeoutMs: number = 90000,
): Promise<AgentResponse[]> {
  const responses: AgentResponse[] = [];
  const startTime = Date.now();

  while (
    responses.length < expectedAgents.length &&
    Date.now() - startTime < timeoutMs
  ) {
    try {
      // Check for new agent responses
      const agentMessages = await page.$$('[data-testid="agent-message"]');

      if (agentMessages.length > responses.length) {
        // Get the latest response
        const latestResponse = await getLatestAgentResponse(page, 5000);

        // Validate it's from an expected agent and quality response
        if (
          expectedAgents.some((agent) =>
            latestResponse.agent.toLowerCase().includes(agent.toLowerCase()),
          ) &&
          validateAIQuality(latestResponse.message)
        ) {
          responses.push(latestResponse);
        }
      }

      // Wait before checking again
      await page.waitForTimeout(2000);
    } catch (error) {
      console.log("Waiting for orchestration step...", error);
      await page.waitForTimeout(3000);
    }
  }

  return responses;
}

/**
 * Login helper for test setup
 */
export async function loginTestUser(page: Page): Promise<void> {
  // For E2E tests, we can bypass login by going directly to agents
  // This simplifies testing the actual AI functionality
  try {
    await page.goto("/agents");
    await page.waitForLoadState("networkidle", { timeout: 5000 });
    return;
  } catch {
    // Fallback to login flow if direct access fails
    await page.goto("/login");

    // Use environment variables for test credentials
    const username = process.env.TEST_USER_USERNAME || "admin@convergio.io";
    const password = process.env.TEST_USER_PASSWORD || "admin123";

    await page.fill('[data-testid="username"]', username);
    await page.fill('[data-testid="password"]', password);
    await page.click('[data-testid="login-button"]');

    // Wait for dashboard or main page
    await page.waitForURL(/\/(dashboard|agents)/, { timeout: 10000 });
  }
}

/**
 * Navigate to specific agent interface
 */
export async function navigateToAgent(
  page: Page,
  agentName: string,
): Promise<void> {
  const agentPath = agentName.toLowerCase().replace(/[^a-z0-9]/g, "_");
  await page.goto(`/agents/${agentPath}`);
  await page.waitForSelector('[data-testid="chat-interface"]', {
    timeout: 15000,
  });
}

/**
 * Clear conversation state for clean tests
 */
export async function clearConversation(page: Page): Promise<void> {
  try {
    // Look for clear/reset button
    const clearButton = page.locator(
      '[data-testid="clear-conversation"], [data-testid="reset-chat"]',
    );
    if (await clearButton.isVisible()) {
      await clearButton.click();
    }

    // Clear any session storage
    await page.evaluate(() => {
      sessionStorage.clear();
      localStorage.removeItem("conversation");
      localStorage.removeItem("chat-history");
    });
  } catch (error) {
    console.log("Could not clear conversation, continuing...", error);
  }
}

/**
 * Check for console errors (should be none for quality tests)
 */
export async function checkConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
    }
  });

  return errors;
}

/**
 * Take screenshot for debugging failures
 */
export async function debugScreenshot(
  page: Page,
  testName: string,
): Promise<void> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  await page.screenshot({
    path: `test-results/debug-${testName}-${timestamp}.png`,
    fullPage: true,
  });
}
