/**
 * Ali Intelligence E2E Tests
 * Tests core Ali (Chief of Staff) capabilities with real AI responses
 * Scenario 1 from testsAug17.md
 */

import { test, expect } from "@playwright/test";
import {
  loginTestUser,
  sendAliQuery,
  getLatestAgentResponse,
  waitForOrchestration,
  clearConversation,
  checkConsoleErrors,
  debugScreenshot,
} from "../utils/agent-helpers";
import {
  expectAIResponse,
  expectBusinessResponse,
  expectOrchestration,
  validateAliResponse,
  validateResearchResponse,
} from "../utils/validation-helpers";
import testData from "../fixtures/test-data.json" with { type: "json" };

test.describe.skip("Ali Intelligence & Strategic Analysis", () => {
  test.beforeEach(async ({ page }) => {
    // Track console errors
    const consoleErrors = await checkConsoleErrors(page);

    // Login and navigate to Ali
    await loginTestUser(page);
    await clearConversation(page);

    // Navigate to Ali's interface
    await page.goto("/agents/ali_chief_of_staff");
    await page.waitForSelector('[data-testid="chat-interface"]', {
      timeout: 10000,
    });
  });

  test("Ali Strategic Analysis - Q4 Growth Strategy", async ({ page }) => {
    const query =
      "Ali, analizza la strategia di crescita per Q4 2024 considerando il mercato AI consulting. Fornisci un'analisi dettagliata con raccomandazioni specifiche, timeline e metriche di successo.";

    const startTime = Date.now();

    // Send strategic query to Ali
    await sendAliQuery(page, query);

    // Wait for comprehensive AI response
    const response = await getLatestAgentResponse(page, 45000); // Extended timeout for complex analysis
    const responseTime = Date.now() - startTime;

    // Validate response quality
    expect(
      validateAliResponse(response),
      `Ali response failed validation: ${response.message.substring(0, 100)}...`,
    ).toBe(true);

    // Business-specific validation
    await expectBusinessResponse(response, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
      hasTimeframes: true,
      hasMetrics: true,
      hasRisksConsideration: true,
    });

    // Performance validation
    expect(responseTime).toBeLessThan(60000); // Max 60 seconds for complex strategy
    expect(response.length).toBeGreaterThan(300); // Substantial strategic analysis

    // Content validation - must include strategic elements
    const content = response.message.toLowerCase();
    expect(content).toContain("q4");
    expect(content).toMatch(/(strategic|strategy)/);
    expect(content).toMatch(/(recommendation|recommend)/);
    expect(content).toMatch(/(growth|expansion)/);

    console.log(`✅ Ali Strategic Analysis completed in ${responseTime}ms`);
    console.log(`📊 Response length: ${response.length} characters`);
  });

  test("Ali Multi-Agent Coordination - Business Plan", async ({ page }) => {
    const query =
      "Ali, coordina Amy (CFO) e Marcus (PM) per creare un business plan completo per il lancio di una nuova piattaforma SaaS. Assicurati che Amy fornisca l'analisi finanziaria e Marcus la pianificazione progettuale.";

    const startTime = Date.now();

    // Send orchestration query
    await sendAliQuery(page, query);

    // Wait for multi-agent orchestration
    const responses = await waitForOrchestration(
      page,
      ["ali", "amy", "marcus"],
      120000,
    );
    const totalTime = Date.now() - startTime;

    // Validate orchestration
    await expectOrchestration(responses);
    expect(responses.length).toBeGreaterThanOrEqual(2); // At least Ali + one other agent

    // Validate Ali's coordination response
    const aliResponse = responses.find((r) =>
      r.agent.toLowerCase().includes("ali"),
    );
    expect(aliResponse).toBeDefined();
    if (aliResponse) {
      await expectBusinessResponse(aliResponse, {
        hasStrategicThinking: true,
        hasActionableInsights: true,
      });
    }

    // Check if financial or project elements are present
    const allContent = responses
      .map((r) => r.message)
      .join(" ")
      .toLowerCase();
    const hasFinancialElements = /budget|cost|revenue|roi|financial/.test(
      allContent,
    );
    const hasProjectElements =
      /timeline|milestone|deliverable|project|plan/.test(allContent);

    expect(
      hasFinancialElements || hasProjectElements,
      "Orchestration should include either financial or project planning elements",
    ).toBe(true);

    // Performance validation
    expect(totalTime).toBeLessThan(150000); // Max 2.5 minutes for orchestration

    console.log(`✅ Multi-agent orchestration completed in ${totalTime}ms`);
    console.log(`🤝 Coordinated ${responses.length} agent responses`);
  });

  test("Ali Research & Internet Search - AI Consulting Trends", async ({
    page,
  }) => {
    const query =
      "Ali, cerca e analizza le ultime tendenze nel settore AI consulting per il 2024-2025. Trova informazioni aggiornate sui competitor, pricing, e opportunità di mercato.";

    const startTime = Date.now();

    // Send research query
    await sendAliQuery(page, query);

    // Wait for research response (includes web search)
    const response = await getLatestAgentResponse(page, 60000); // Extended for web research
    const responseTime = Date.now() - startTime;

    // Validate research response
    expect(
      validateResearchResponse(response),
      `Research response failed validation: ${response.message.substring(0, 100)}...`,
    ).toBe(true);

    // Should contain current/recent information
    const content = response.message.toLowerCase();
    expect(content).toMatch(/(2024|2025)/); // Current year references
    expect(content).toMatch(/(trend|trending|latest|recent|current)/);
    expect(content).toMatch(/(ai|artificial intelligence|consulting)/);

    // Business intelligence validation
    await expectBusinessResponse(response, {
      hasStrategicThinking: true,
      hasDataDriven: true,
      hasActionableInsights: true,
    });

    // Performance validation
    expect(responseTime).toBeLessThan(90000); // Max 90 seconds for web research
    expect(response.length).toBeGreaterThan(400); // Comprehensive research

    console.log(`✅ Research analysis completed in ${responseTime}ms`);
    console.log(`🔍 Response includes web research and analysis`);
  });

  test("Ali Decision Making - Complex Business Scenario", async ({ page }) => {
    const scenario = testData.business_scenarios.strategic_expansion;
    const query = `Ali, valuta questo scenario: ${scenario.description}. 
    Contesto: mercati attuali ${scenario.context.current_markets.join(", ")}, 
    target ${scenario.context.target_markets.join(", ")}, 
    budget ${scenario.context.budget_range}, 
    timeline ${scenario.context.timeline}. 
    Fornisci un'analisi completa con raccomandazioni strategiche, considerazioni sui rischi e piano di implementazione.`;

    const startTime = Date.now();

    // Send complex scenario
    await sendAliQuery(page, query);

    // Wait for comprehensive analysis
    const response = await getLatestAgentResponse(page, 60000);
    const responseTime = Date.now() - startTime;

    // Validate comprehensive response
    await expectBusinessResponse(response, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
      hasRisksConsideration: true,
      hasTimeframes: true,
      hasDataDriven: true,
    });

    // Validate scenario-specific content
    const content = response.message.toLowerCase();

    // Should reference the markets mentioned
    const hasTargetMarkets = scenario.context.target_markets.some((market) =>
      content.includes(market.toLowerCase()),
    );
    expect(hasTargetMarkets, "Response should reference target markets").toBe(
      true,
    );

    // Should include risk analysis
    expect(content).toMatch(/(risk|challenge|obstacle|threat)/);

    // Should include actionable recommendations
    expect(content).toMatch(/(recommend|suggest|propose|action|implement)/);

    // Performance and quality
    expect(responseTime).toBeLessThan(90000);
    expect(response.length).toBeGreaterThan(500); // Very comprehensive for complex scenario

    console.log(`✅ Complex scenario analysis completed in ${responseTime}ms`);
    console.log(`📈 Comprehensive business analysis provided`);
  });

  test("Ali Continuous Context - Follow-up Questions", async ({ page }) => {
    // First query - establish context
    const initialQuery =
      "Ali, analizza il mercato delle piattaforme di analytics B2B.";
    await sendAliQuery(page, initialQuery);

    const initialResponse = await getLatestAgentResponse(page, 45000);
    expect(validateAliResponse(initialResponse)).toBe(true);

    // Follow-up query - test context retention
    const followupQuery =
      "Basandoti sull'analisi precedente, quali sono le 3 opportunità principali per una startup in questo settore?";
    await sendAliQuery(page, followupQuery);

    const followupResponse = await getLatestAgentResponse(page, 30000);

    // Validate follow-up maintains context
    expect(validateAliResponse(followupResponse)).toBe(true);

    // Should reference previous analysis
    const content = followupResponse.message.toLowerCase();
    expect(content).toMatch(/(opportunity|opportunità)/);
    expect(content).toMatch(/(startup|nuova|nuovo)/);

    // Should have specific recommendations
    expect(content).toMatch(/[1-3]\.|\bullet|•/); // Numbered or bulleted list

    console.log("✅ Context retention and follow-up validated");
  });

  test.afterEach(async ({ page }) => {
    // Take screenshot on failure for debugging
    if (test.info().status === "failed") {
      await debugScreenshot(page, `ali-intelligence-${test.info().title}`);
    }

    // Check for console errors
    const errors = await page.evaluate(() => {
      return window.consoleErrors || [];
    });

    if (errors.length > 0) {
      console.warn(`Console errors detected: ${errors.join(", ")}`);
      // Don't fail test for console errors, but log them
    }
  });
});
