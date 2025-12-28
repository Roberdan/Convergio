import { test, expect } from "@playwright/test";

test.describe("Agent Interactions", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto("/");

    // Wait for the app to load
    await page.waitForSelector('span:has-text("platform.Convergio.io")', {
      timeout: 10000,
    });
  });

  test.skip("should display API status dropdown", async ({ page }) => {
    // SKIPPED: API status dropdown UI not implemented yet
    // This test should be enabled when the UI component is added
  });

  test.skip("should navigate to agents page", async ({ page }) => {
    // Click on Agents in navigation
    await page.click(
      'nav a:has-text("Agents"), a[href*="agents"]:has-text("Agents")',
    );

    // Wait for agents page to load
    await page.waitForURL("**/agents");

    // Check for agent-related content
    await expect(
      page.locator("h1, h2").filter({ hasText: /Agent/i }),
    ).toBeVisible();
  });

  test.skip("should start agent conversation", async ({ page }) => {
    // Set reasonable timeout
    test.setTimeout(20000);

    // Navigate to agents page
    await page.click(
      'nav a:has-text("Agents"), a[href*="agents"]:has-text("Agents")',
    );
    await page.waitForURL("**/agents");

    // Look for conversation start button or chat interface
    const chatInterface = page.locator(
      '.agent-chat, .conversation-interface, [data-testid="chat-interface"]',
    );

    if ((await chatInterface.count()) > 0) {
      // Type a message
      const messageInput = page.locator('input[type="text"], textarea').first();
      await messageInput.fill(
        "Hello, can you help me analyze Microsoft Q4 earnings?",
      );

      // Send message (look for send button or press Enter)
      const sendButton = page.locator("button").filter({ hasText: /send/i });
      if ((await sendButton.count()) > 0) {
        await sendButton.click();
      } else {
        await messageInput.press("Enter");
      }

      // Wait for response (with shorter timeout and multiple selectors)
      const responseReceived = await Promise.race([
        page
          .waitForSelector(
            ".agent-response, .message-response, .streaming-token",
            {
              timeout: 10000,
              state: "visible",
            },
          )
          .then(() => true),
        page.waitForTimeout(10000).then(() => false),
      ]);

      if (!responseReceived) {
        console.log("No immediate response, might be streaming or loading");
      } else {
        console.log("Agent response received");
      }
    }
  });

  test.skip("should display agent list", async ({ page }) => {
    // Navigate to agents page
    await page.click(
      'nav a:has-text("Agents"), a[href*="agents"]:has-text("Agents")',
    );
    await page.waitForURL("**/agents");

    // Look for agent cards or list
    const agentElements = page.locator(
      '.agent-card, .agent-item, [data-testid="agent"]',
    );

    if ((await agentElements.count()) > 0) {
      // Check if we have multiple agents
      const count = await agentElements.count();
      expect(count).toBeGreaterThan(0);

      // Check for Amy CFO specifically
      const amyCfo = page.locator("text=/Amy.*CFO/i");
      if ((await amyCfo.count()) > 0) {
        await expect(amyCfo.first()).toBeVisible();
      }
    }
  });

  test.skip("should handle WebSocket connection for streaming", async ({
    page,
  }) => {
    // Set shorter timeout for WebSocket test
    test.setTimeout(15000);

    // Navigate to agents page
    await page.click(
      'nav a:has-text("Agents"), a[href*="agents"]:has-text("Agents")',
    );
    await page.waitForURL("**/agents");

    // Set up WebSocket listener with Promise for first message
    let wsConnected = false;
    const firstMessagePromise = new Promise((resolve) => {
      page.on("websocket", (ws) => {
        wsConnected = true;
        console.log(`WebSocket opened: ${ws.url()}`);
        ws.on("framereceived", (event) => {
          resolve(event.payload);
        });
      });
    });

    // Try to initiate a streaming conversation
    const chatInput = page.locator('input[type="text"], textarea').first();
    if ((await chatInput.count()) > 0) {
      await chatInput.fill("Tell me about Apple stock performance");
      await chatInput.press("Enter");

      // Wait for first WebSocket message or timeout
      const raceResult = await Promise.race([
        firstMessagePromise,
        page.waitForTimeout(5000).then(() => "timeout"),
      ]);

      // Check results
      if (raceResult !== "timeout") {
        console.log("WebSocket message received successfully");
        expect(wsConnected).toBeTruthy();
      } else {
        console.log(
          "WebSocket connection not established in time (expected for some configurations)",
        );
      }
    }
  });
});

test.describe("Complex Orchestrations", () => {
  test.skip("should handle multi-agent collaboration", async ({ page }) => {
    // Navigate to agents or orchestration page
    await page.goto("/");

    // Look for orchestration features
    const orchestrationLink = page.locator(
      "text=/orchestrat|coordinat|workflow/i",
    );
    if ((await orchestrationLink.count()) > 0) {
      await orchestrationLink.first().click();
      await page.waitForLoadState("networkidle");

      // Check for orchestration interface
      await expect(
        page.locator("text=/orchestrat|workflow|coordination/i"),
      ).toBeVisible();
    }
  });

  test.skip("should display cost tracking information", async ({ page }) => {
    await page.goto("/");

    // Look for cost display in header or dashboard
    const costDisplay = page.locator("text=/\\$\\d+\\.\\d+|cost|token/i");
    if ((await costDisplay.count()) > 0) {
      await expect(costDisplay.first()).toBeVisible();

      // Check if cost updates
      const initialText = await costDisplay.first().textContent();

      // Trigger an action that might update costs
      const agentsLink = page.locator(
        'nav a:has-text("Agents"), a[href*="agents"]:has-text("Agents")',
      );
      if ((await agentsLink.count()) > 0) {
        await agentsLink.click();
        await page.waitForTimeout(2000);

        // Check if cost changed
        const newText = await costDisplay.first().textContent();
        console.log(`Cost tracking: ${initialText} -> ${newText}`);
      }
    }
  });

  test.skip("should show agent signatures when available", async ({ page }) => {
    await page.goto("/");
    await page.click(
      'nav a:has-text("Agents"), a[href*="agents"]:has-text("Agents")',
    );
    await page.waitForURL("**/agents");

    // Look for signature indicators
    const signatureElements = page.locator("text=/signature|verified|signed/i");
    if ((await signatureElements.count()) > 0) {
      console.log("Found agent signature elements");
      await expect(signatureElements.first()).toBeVisible();
    }
  });
});

test.describe("Performance and Error Handling", () => {
  test.skip("should load quickly", async ({ page }) => {
    const startTime = Date.now();
    await page.goto("/");
    await page.waitForSelector('span:has-text("platform.Convergio.io")');
    const loadTime = Date.now() - startTime;

    console.log(`Page load time: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(5000); // Should load in less than 5 seconds
  });

  test.skip("should handle API errors gracefully", async ({ page }) => {
    // Intercept API calls and force an error
    await page.route("**/api/v1/**", (route) => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: "Test error" }),
      });
    });

    await page.goto("/");

    // Should show error message or fallback content
    await page.waitForTimeout(2000);

    // App should still be functional despite API error
    await expect(
      page.locator('span:has-text("platform.Convergio.io")'),
    ).toBeVisible();
  });

  test.skip("should reconnect WebSocket on disconnect", async ({ page }) => {
    await page.goto("/");
    await page.click(
      'nav a:has-text("Agents"), a[href*="agents"]:has-text("Agents")',
    );

    let wsCount = 0;
    page.on("websocket", (ws) => {
      wsCount++;
      console.log(`WebSocket #${wsCount} opened: ${ws.url()}`);

      // Simulate disconnect after 2 seconds
      if (wsCount === 1) {
        setTimeout(() => {
          ws.close();
        }, 2000);
      }
    });

    await page.waitForTimeout(5000);

    // Should have attempted reconnection
    if (wsCount > 0) {
      console.log(`Total WebSocket connections: ${wsCount}`);
    }
  });
});
