/**
 * Business Operations E2E Tests
 * Tests project management, talent management, and financial analysis workflows
 * Scenario 2 from testsAug17.md
 */

import { test, expect } from "@playwright/test";
import {
  loginTestUser,
  sendAgentQuery,
  sendAliQuery,
  getLatestAgentResponse,
  waitForOrchestration,
  clearConversation,
  navigateToAgent,
  debugScreenshot,
} from "../utils/agent-helpers";
import {
  expectAIResponse,
  expectBusinessResponse,
  validateAmyFinancialResponse,
  validateMarcusProjectResponse,
} from "../utils/validation-helpers";
import testData from "../fixtures/test-data.json" with { type: "json" };

test.describe.skip("Business Operations & Project Management", () => {
  test.beforeEach(async ({ page }) => {
    await loginTestUser(page);
    await clearConversation(page);
  });

  test("Project Creation & Management with Marcus PM", async ({ page }) => {
    // Navigate to Marcus (Project Manager)
    await navigateToAgent(page, "marcus_pm");

    const projectQuery = `Marcus, crea una roadmap dettagliata per il lancio di una nuova piattaforma SaaS di analytics B2B. 
    Include: timeline di 6 mesi, milestone principali, risorse necessarie, deliverable per ogni fase, 
    e criteri di successo. Il team include 5 sviluppatori, 2 designers, 1 PM.`;

    const startTime = Date.now();

    // Send project planning query
    await sendAgentQuery(page, "marcus_pm", projectQuery);

    // Wait for comprehensive project response
    const response = await getLatestAgentResponse(page, 45000);
    const responseTime = Date.now() - startTime;

    // Validate Marcus PM response
    expect(
      validateMarcusProjectResponse(response),
      `Marcus PM response failed validation: ${response.message.substring(0, 100)}...`,
    ).toBe(true);

    // Business validation for project management
    await expectBusinessResponse(response, {
      hasActionableInsights: true,
      hasTimeframes: true,
      hasDataDriven: true,
    });

    // Project-specific validations
    const content = response.message.toLowerCase();

    // Should include timeline elements
    expect(content).toMatch(/(month|settimana|week|fase|phase)/);
    expect(content).toMatch(/(milestone|deliverable|obiettivo)/);
    expect(content).toMatch(/(roadmap|timeline|planning)/);

    // Should include resource considerations
    expect(content).toMatch(/(team|risorse|resource|sviluppatori|designer)/);

    // Should have structured planning
    expect(response.message).toMatch(/[1-6]\.|\bullet|•/); // Numbered phases or bullets

    // Performance validation
    expect(responseTime).toBeLessThan(60000);
    expect(response.length).toBeGreaterThan(300);

    console.log(`✅ Project roadmap created in ${responseTime}ms`);
    console.log(`📋 Response includes timeline and resource planning`);
  });

  test("Talent & Resource Management with Giulia HR", async ({ page }) => {
    // Navigate to Giulia (HR Talent Acquisition)
    await navigateToAgent(page, "giulia_hr_talent_acquisition");

    const talentQuery = `Giulia, per il progetto di piattaforma analytics AI che abbiamo discusso, 
    identifica i profili professionali ideali che dovremmo assumere. 
    Includi: competenze tecniche richieste, seniority level, budget range per ruolo, 
    strategie di recruiting, e timeline per le assunzioni. Focus su AI/ML engineers, 
    full-stack developers, e product designers.`;

    const startTime = Date.now();

    await sendAgentQuery(page, "giulia_hr_talent_acquisition", talentQuery);

    const response = await getLatestAgentResponse(page, 40000);
    const responseTime = Date.now() - startTime;

    // Validate HR response quality
    await expectAIResponse(response, {
      minLength: 200,
      mustHaveStructure: true,
      mustContain: ["competenze", "profilo", "recruiting"],
    });

    // Business validation for talent management
    await expectBusinessResponse(response, {
      hasActionableInsights: true,
      hasDataDriven: true,
      hasTimeframes: true,
    });

    // HR-specific validations
    const content = response.message.toLowerCase();

    // Should include role-specific information
    expect(content).toMatch(/(ai|ml|machine learning|full.stack|designer)/);
    expect(content).toMatch(/(competenze|skills|esperienza|experience)/);
    expect(content).toMatch(/(recruiting|assunzione|hiring)/);

    // Should include practical hiring guidance
    expect(content).toMatch(/(budget|salary|stipendio|costo)/);
    expect(content).toMatch(/(timeline|tempo|durata)/);

    // Performance validation
    expect(responseTime).toBeLessThan(50000);
    expect(response.length).toBeGreaterThan(250);

    console.log(`✅ Talent analysis completed in ${responseTime}ms`);
    console.log(`👥 HR recommendations provided`);
  });

  test("Financial Analysis with Amy CFO", async ({ page }) => {
    // Navigate to Amy (CFO)
    await navigateToAgent(page, "amy_cfo");

    const financialQuery = `Amy, analizza il budget e calcola il ROI previsto per il progetto piattaforma SaaS analytics. 
    Parametri: budget sviluppo $800K, costi operativi annuali $200K, prezzo subscription $199/mese per utente, 
    target 500 clienti primo anno, 1200 secondo anno. 
    Include: break-even analysis, cash flow projection, sensitivity analysis sui key metrics.`;

    const startTime = Date.now();

    await sendAgentQuery(page, "amy_cfo", financialQuery);

    const response = await getLatestAgentResponse(page, 50000);
    const responseTime = Date.now() - startTime;

    // Validate Amy CFO response
    expect(
      validateAmyFinancialResponse(response),
      `Amy CFO response failed validation: ${response.message.substring(0, 100)}...`,
    ).toBe(true);

    // Business validation for financial analysis
    await expectBusinessResponse(response, {
      hasDataDriven: true,
      hasMetrics: true,
      hasActionableInsights: true,
      hasRisksConsideration: true,
    });

    // Financial-specific validations
    const content = response.message.toLowerCase();

    // Should include financial metrics
    expect(content).toMatch(/(roi|return|ritorno)/);
    expect(content).toMatch(/(break.even|pareggio|breakeven)/);
    expect(content).toMatch(/(cash flow|flusso|liquidità)/);

    // Should include numerical analysis
    expect(response.message).toMatch(/\$[\d,]+|\d+%|\d+k/); // Money or percentages
    expect(response.message).toMatch(/\d+/); // Numbers

    // Should reference the given parameters
    expect(content).toMatch(/(800|199|500|1200)/); // Key numbers from query

    // Performance validation
    expect(responseTime).toBeLessThan(60000);
    expect(response.length).toBeGreaterThan(300);

    console.log(`✅ Financial analysis completed in ${responseTime}ms`);
    console.log(`💰 ROI and budget analysis provided`);
  });

  test("Integrated Business Workflow - Ali Coordinates Project Team", async ({
    page,
  }) => {
    // This tests Ali coordinating Marcus, Amy, and Giulia for a complete business workflow
    await navigateToAgent(page, "ali_chief_of_staff");

    const scenario = testData.business_scenarios.product_launch;
    const integratedQuery = `Ali, coordina Marcus (PM), Amy (CFO), e Giulia (HR) per pianificare completamente 
    il lancio di ${scenario.title}. 
    Contesto: ${scenario.description}, timeline ${scenario.context.timeline}, budget ${scenario.context.budget}.
    
    Assicurati che:
    - Marcus fornisca la roadmap dettagliata
    - Amy analizzi budget, costi e ROI 
    - Giulia definisca il piano di hiring
    - Tu coordini tutto e fornisci la strategia generale`;

    const startTime = Date.now();

    await sendAliQuery(page, integratedQuery);

    // Wait for complex multi-agent orchestration
    const responses = await waitForOrchestration(
      page,
      ["ali", "marcus", "amy", "giulia"],
      180000,
    );
    const totalTime = Date.now() - startTime;

    // Validate orchestration success
    expect(responses.length).toBeGreaterThanOrEqual(2);

    // Validate Ali's coordination
    const aliResponse = responses.find((r) =>
      r.agent.toLowerCase().includes("ali"),
    );
    expect(aliResponse).toBeDefined();

    if (aliResponse) {
      await expectBusinessResponse(aliResponse, {
        hasStrategicThinking: true,
        hasActionableInsights: true,
        hasTimeframes: true,
      });
    }

    // Check for cross-functional content
    const allContent = responses
      .map((r) => r.message)
      .join(" ")
      .toLowerCase();

    // Should have project elements
    const hasProjectContent = /roadmap|timeline|milestone|deliverable/.test(
      allContent,
    );

    // Should have financial elements
    const hasFinancialContent = /budget|cost|roi|revenue|financial/.test(
      allContent,
    );

    // Should have HR elements
    const hasHRContent = /hiring|talent|team|competenze|recruiting/.test(
      allContent,
    );

    // At least 2 of 3 functional areas should be covered
    const functionalCoverage = [
      hasProjectContent,
      hasFinancialContent,
      hasHRContent,
    ].filter(Boolean).length;
    expect(functionalCoverage).toBeGreaterThanOrEqual(2);

    // Performance validation for complex workflow
    expect(totalTime).toBeLessThan(240000); // Max 4 minutes for complex orchestration

    console.log(`✅ Integrated business workflow completed in ${totalTime}ms`);
    console.log(`🎯 ${responses.length} agents coordinated successfully`);
    console.log(
      `📊 Functional coverage: Project=${hasProjectContent}, Finance=${hasFinancialContent}, HR=${hasHRContent}`,
    );
  });

  test("Business Data Persistence - Project Information Storage", async ({
    page,
  }) => {
    // Test that business information is properly stored and retrievable
    await navigateToAgent(page, "marcus_pm");

    const projectName = `TestProject_${Date.now()}`;
    const createProjectQuery = `Marcus, crea un nuovo progetto chiamato "${projectName}" 
    per sviluppo di dashboard analytics. Timeline: 4 mesi, budget: $300K, team: 6 persone. 
    Salva tutte le informazioni del progetto.`;

    await sendAgentQuery(page, "marcus_pm", createProjectQuery);
    const createResponse = await getLatestAgentResponse(page, 30000);

    expect(validateMarcusProjectResponse(createResponse)).toBe(true);
    expect(createResponse.message.toLowerCase()).toContain(
      projectName.toLowerCase(),
    );

    // Wait a moment, then try to retrieve project information
    await page.waitForTimeout(3000);

    const retrieveQuery = `Marcus, mostrami i dettagli del progetto "${projectName}" che abbiamo appena creato.`;
    await sendAgentQuery(page, "marcus_pm", retrieveQuery);
    const retrieveResponse = await getLatestAgentResponse(page, 20000);

    // Should remember the project
    expect(retrieveResponse.message.toLowerCase()).toContain(
      projectName.toLowerCase(),
    );
    expect(retrieveResponse.message.toLowerCase()).toMatch(
      /(300k|dashboard|4 mesi|6 persone)/,
    );

    console.log(`✅ Project information persisted and retrieved successfully`);
  });

  test.afterEach(async ({ page }) => {
    if (test.info().status === "failed") {
      await debugScreenshot(page, `business-operations-${test.info().title}`);
    }
  });
});
