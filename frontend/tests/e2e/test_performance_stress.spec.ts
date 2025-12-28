/**
 * Performance & Stress Testing E2E Tests
 * Tests concurrent multi-agent sessions and complex orchestration workflows
 * Scenario 5 from testsAug17.md - Performance validation
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
} from "../utils/validation-helpers";
import testData from "../fixtures/test-data.json" with { type: "json" };

test.describe("Performance & Stress Testing", () => {
  test.beforeEach(async ({ page }) => {
    await loginTestUser(page);
    await clearConversation(page);
  });

  test("Concurrent Multi-Agent Sessions - 5 Simultaneous Queries", async ({
    page,
  }) => {
    // Test concurrent processing capabilities
    const queries = [
      {
        agent: "ali_chief_of_staff",
        query:
          "Ali, analizza velocemente il market sizing per SaaS analytics in Europa.",
      },
      {
        agent: "amy_cfo",
        query:
          "Amy, calcola ROI per investimento $500K in marketing con 25% conversion rate.",
      },
      {
        agent: "baccio_tech_architect",
        query:
          "Baccio, consiglia stack tecnologico per MVP di marketplace B2B.",
      },
      {
        agent: "sara_ux_ui_designer",
        query: "Sara, progetta user flow per onboarding di app mobile fintech.",
      },
      {
        agent: "marcus_pm",
        query:
          "Marcus, crea timeline per lancio prodotto con team di 8 persone in 12 settimane.",
      },
    ];

    const startTime = Date.now();
    const promises: Promise<any>[] = [];

    // Start all queries concurrently
    for (const { agent, query } of queries) {
      const promise = (async () => {
        await navigateToAgent(page, agent);
        await sendAgentQuery(page, agent, query);
        return await getLatestAgentResponse(page, 45000);
      })();
      promises.push(promise);
    }

    // Wait for all responses
    const responses = await Promise.all(promises);
    const totalTime = Date.now() - startTime;

    // Validate all responses received
    expect(responses.length).toBe(5);

    // Validate each response quality
    for (let i = 0; i < responses.length; i++) {
      const response = responses[i];
      expect(response).toBeTruthy();
      expect(response.message).toBeTruthy();
      expect(response.message.length).toBeGreaterThan(100);

      // Each response should be relevant to its query
      const queryKeywords = queries[i].query.toLowerCase();
      const responseContent = response.message.toLowerCase();

      if (queryKeywords.includes("market")) {
        expect(responseContent).toMatch(
          /(market|sizing|europa|analytics|saas)/,
        );
      } else if (queryKeywords.includes("roi")) {
        expect(responseContent).toMatch(
          /(roi|return|invest|marketing|conversion)/,
        );
      } else if (queryKeywords.includes("stack")) {
        expect(responseContent).toMatch(/(stack|technolog|mvp|marketplace)/);
      } else if (queryKeywords.includes("user flow")) {
        expect(responseContent).toMatch(/(user|flow|onboard|mobile|fintech)/);
      } else if (queryKeywords.includes("timeline")) {
        expect(responseContent).toMatch(
          /(timeline|settimana|team|lancio|prodotto)/,
        );
      }
    }

    // Performance validation
    expect(totalTime).toBeLessThan(90000); // Max 90 seconds for 5 concurrent queries

    // Calculate average response time
    const avgResponseTime = totalTime / 5;
    expect(avgResponseTime).toBeLessThan(20000); // Average under 20 seconds per query

    console.log(
      `✅ Concurrent multi-agent sessions completed in ${totalTime}ms`,
    );
    console.log(`⚡ Average response time: ${avgResponseTime}ms per agent`);
    console.log(
      `🔄 All 5 agents responded successfully with quality responses`,
    );
  });

  test("Complex Orchestration Workflow - End-to-End Agent Chain", async ({
    page,
  }) => {
    // Test complex workflow: Ali → Marcus → Amy → Baccio → Sara
    await navigateToAgent(page, "ali_chief_of_staff");

    const complexQuery = `Ali, coordina un workflow complesso per il progetto "FinanceFlow SaaS":

    1. Marcus (PM): Crea roadmap dettagliata per 6 mesi di sviluppo
    2. Amy (CFO): Analizza budget necessario e proiezioni revenue
    3. Baccio (Tech): Definisci architettura scalabile per 100K+ utenti
    4. Sara (UX): Progetta user experience per dashboard executive

    Ogni agent deve costruire sul lavoro del precedente. Voglio un handoff fluido e risultato finale coerente.`;

    const startTime = Date.now();

    await sendAliQuery(page, complexQuery);

    // Wait for complex orchestration (extended timeout)
    const responses = await waitForOrchestration(page, ["ali"], 240000); // 4 minutes max
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const orchestrationResponse = responses[0];
    const content = orchestrationResponse.message.toLowerCase();

    // Should demonstrate complex workflow coordination
    expect(content).toMatch(/(workflow|orchestrat|coordinat|handoff)/);
    expect(content).toMatch(/(marcus|amy|baccio|sara)/); // Agent references
    expect(content).toMatch(
      /(roadmap.*budget|budget.*architect|architect.*ux|pm.*cfo.*tech.*ux)/,
    ); // Sequential workflow

    // Should include elements from each domain
    const hasProjectManagement =
      /roadmap|timeline|milestone|sviluppo|6.mesi/.test(content);
    const hasFinancialAnalysis = /budget|revenue|financial|proiezion|cost/.test(
      content,
    );
    const hasTechnicalArchitecture =
      /architect|scalab|100k|technical|infrastructure/.test(content);
    const hasUXDesign = /ux|user.experience|dashboard|executive|design/.test(
      content,
    );

    const workflowSteps = [
      hasProjectManagement,
      hasFinancialAnalysis,
      hasTechnicalArchitecture,
      hasUXDesign,
    ].filter(Boolean).length;
    expect(workflowSteps).toBeGreaterThanOrEqual(3); // Should cover most workflow steps

    // Should demonstrate integration and coherence
    expect(content).toMatch(/(integrat|coher|consistent|build.on|based.on)/);

    // Validate business quality for complex orchestration
    await expectBusinessResponse(orchestrationResponse, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
      hasTimeframes: true,
      hasDataDriven: true,
    });

    // Performance validation for complex workflow
    expect(totalTime).toBeLessThan(300000); // Max 5 minutes for complex orchestration
    expect(orchestrationResponse.length).toBeGreaterThan(600);

    console.log(
      `✅ Complex orchestration workflow completed in ${totalTime}ms`,
    );
    console.log(
      `🔗 Workflow steps: PM=${hasProjectManagement}, Finance=${hasFinancialAnalysis}, Tech=${hasTechnicalArchitecture}, UX=${hasUXDesign}`,
    );
    console.log(`🎯 Integrated workflow with handoff coordination successful`);
  });

  test("High-Complexity Business Scenario - Fortune 500 Digital Transformation", async ({
    page,
  }) => {
    // Test handling of extremely complex business scenarios
    await navigateToAgent(page, "ali_chief_of_staff");

    const megaComplexQuery = `Ali, siamo una Fortune 500 manufacturing company che deve eseguire 
    una digital transformation completa. Coordina tutto il tuo ecosystem per questo mega-progetto:

    CONTESTO:
    - 50,000 dipendenti in 15 paesi
    - Legacy systems da modernizzare (ERP SAP da anni '90)  
    - Compliance multi-country (GDPR, SOX, FDA per healthcare division)
    - Budget $50M, timeline 24 mesi
    - Resistenza al cambiamento culturale significativa

    OBIETTIVI:
    - Cloud-first architecture con Azure/AWS
    - AI/ML per predictive maintenance e supply chain
    - Modern data platform per real-time insights
    - Digital workplace transformation (Microsoft 365)
    - Cybersecurity posture improvement
    - Change management per adoption

    Coordina TUTTO il team: Strategy, Tech, Finance, Security, HR, Change Management, Data, PM.
    Voglio una solution completa e enterprise-ready.`;

    const startTime = Date.now();

    await sendAliQuery(page, megaComplexQuery);

    const responses = await waitForOrchestration(page, ["ali"], 300000); // 5 minutes max for mega complexity
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const megaResponse = responses[0];
    const content = megaResponse.message.toLowerCase();

    // Should handle Fortune 500 complexity
    expect(content).toMatch(
      /(fortune.500|enterprise|digital.transformation|manufacturing)/,
    );
    expect(content).toMatch(/(50000|50,000|15.paesi|50m|24.mesi)/); // Scale references
    expect(content).toMatch(/(legacy|sap|erp|moderniz)/);

    // Should address major transformation areas
    const hasStrategy = /strateg|transformation|digital|vision/.test(content);
    const hasTechnology = /cloud|azure|aws|architect|ai|ml|data.platform/.test(
      content,
    );
    const hasFinancial = /budget|50m|cost|roi|investment/.test(content);
    const hasSecurity = /security|cybersecurity|compliance|gdpr|sox/.test(
      content,
    );
    const hasChangeManagement =
      /change.management|resistance|adoption|cultural/.test(content);
    const hasCompliance = /compliance|multi.country|gdpr|sox|fda/.test(content);

    const transformationAreas = [
      hasStrategy,
      hasTechnology,
      hasFinancial,
      hasSecurity,
      hasChangeManagement,
      hasCompliance,
    ].filter(Boolean).length;
    expect(transformationAreas).toBeGreaterThanOrEqual(4); // Should cover most transformation areas

    // Should demonstrate enterprise-level thinking
    expect(content).toMatch(/(enterprise|scale|global|multi.country)/);
    expect(content).toMatch(/(governance|framework|methodology)/);
    expect(content).toMatch(/(phase|milestone|workstream|program)/);

    // Should be comprehensive and actionable
    await expectBusinessResponse(megaResponse, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
      hasTimeframes: true,
      hasRisksConsideration: true,
      hasDataDriven: true,
    });

    // Performance validation for mega complexity
    expect(totalTime).toBeLessThan(360000); // Max 6 minutes for Fortune 500 digital transformation
    expect(megaResponse.length).toBeGreaterThan(800);

    console.log(
      `✅ Fortune 500 digital transformation planning completed in ${totalTime}ms`,
    );
    console.log(
      `🏢 Transformation areas: Strategy=${hasStrategy}, Tech=${hasTechnology}, Finance=${hasFinancial}, Security=${hasSecurity}, Change=${hasChangeManagement}, Compliance=${hasCompliance}`,
    );
    console.log(`🌍 Enterprise-scale complexity handled successfully`);
  });

  test("Stress Test - Rapid-Fire Query Sequence", async ({ page }) => {
    // Test system resilience with rapid consecutive queries
    await navigateToAgent(page, "ali_chief_of_staff");

    const rapidQueries = [
      "Ali, quick market analysis per SaaS analytics.",
      "Ali, recommend pricing strategy per competitor a $99/month.",
      "Ali, evaluate acquisition target: revenue $2M, growth 50%.",
      "Ali, assess technical debt impact on product roadmap.",
      "Ali, prioritize feature backlog per customer feedback.",
      "Ali, calculate team scaling needs per 200% growth target.",
      "Ali, evaluate partnership opportunity con Microsoft.",
      "Ali, assess compliance requirements per EU expansion.",
    ];

    const startTime = Date.now();
    const responseTimes: number[] = [];

    // Send queries in rapid succession
    for (let i = 0; i < rapidQueries.length; i++) {
      const queryStart = Date.now();

      await sendAliQuery(page, rapidQueries[i]);
      const response = await getLatestAgentResponse(page, 30000);

      const queryTime = Date.now() - queryStart;
      responseTimes.push(queryTime);

      // Validate response quality even under stress
      expect(response).toBeTruthy();
      expect(response.message.length).toBeGreaterThan(50);

      // Brief pause between queries
      await page.waitForTimeout(1000);
    }

    const totalTime = Date.now() - startTime;

    // Performance validation
    const avgResponseTime =
      responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    const maxResponseTime = Math.max(...responseTimes);

    expect(avgResponseTime).toBeLessThan(25000); // Average under 25 seconds
    expect(maxResponseTime).toBeLessThan(40000); // No single query over 40 seconds
    expect(totalTime).toBeLessThan(300000); // Total under 5 minutes

    // Consistency validation - no degradation over time
    const firstHalfAvg =
      responseTimes.slice(0, 4).reduce((a, b) => a + b, 0) / 4;
    const secondHalfAvg = responseTimes.slice(4).reduce((a, b) => a + b, 0) / 4;
    const degradationRatio = secondHalfAvg / firstHalfAvg;

    expect(degradationRatio).toBeLessThan(1.5); // No more than 50% performance degradation

    console.log(`✅ Stress test completed in ${totalTime}ms`);
    console.log(`⚡ Average response time: ${avgResponseTime.toFixed(0)}ms`);
    console.log(
      `📊 Performance consistency: ${(degradationRatio * 100).toFixed(1)}% degradation ratio`,
    );
    console.log(
      `🔥 ${rapidQueries.length} rapid-fire queries handled successfully`,
    );
  });

  test("Memory and Context Persistence Under Load", async ({ page }) => {
    // Test memory persistence during intensive operations
    await navigateToAgent(page, "ali_chief_of_staff");

    // Set context
    const contextQuery = `Ali, ricorda questi dettagli del nostro progetto "Phoenix":
    - Budget: $2.5M
    - Timeline: 18 mesi
    - Team: 12 developers, 3 designers, 2 PMs
    - Stack: React, Node.js, PostgreSQL, AWS
    - Target: B2B SaaS per supply chain management
    - Launch date: Q2 2025`;

    await sendAliQuery(page, contextQuery);
    const contextResponse = await getLatestAgentResponse(page, 20000);
    expect(contextResponse.message.toLowerCase()).toMatch(
      /(phoenix|ricord|understand|noted)/,
    );

    // Perform intensive operations
    const intensiveQueries = [
      "Ali, analizza 5 competitors nel supply chain management.",
      "Ali, calcola complex financial projections per 3 anni.",
      "Ali, crea detailed technical architecture per scalabilità.",
      "Ali, sviluppa comprehensive go-to-market strategy.",
    ];

    // Execute intensive operations
    for (const query of intensiveQueries) {
      await sendAliQuery(page, query);
      await getLatestAgentResponse(page, 60000);
      await page.waitForTimeout(2000);
    }

    // Test context recall after intensive operations
    const memoryTestQuery = `Ali, basandoti sui dettagli del progetto Phoenix che ti ho dato prima, 
    calcola il cost per developer per month e valuta se il budget è sufficiente.`;

    await sendAliQuery(page, memoryTestQuery);
    const memoryResponse = await getLatestAgentResponse(page, 30000);
    const memoryContent = memoryResponse.message.toLowerCase();

    // Should recall project context correctly
    expect(memoryContent).toMatch(
      /(phoenix|2\.5m|2\.5.milioni|12.developer|18.mesi)/,
    );
    expect(memoryContent).toMatch(
      /(budget|cost.per.developer|sufficient|sufficiente)/,
    );
    expect(memoryContent).toMatch(/(\$|budget|financial|calculation)/);

    // Should perform calculations based on remembered context
    expect(memoryContent).toMatch(/(calcul|math|per.month|monthly|mensile)/);

    await expectAIResponse(memoryResponse, {
      minLength: 150,
      mustContain: ["phoenix", "budget"],
    });

    console.log(`✅ Memory and context persistence test passed`);
    console.log(`🧠 Context retained accurately through intensive operations`);
    console.log(
      `📝 Complex calculations performed with remembered project details`,
    );
  });

  test.afterEach(async ({ page }) => {
    if (test.info().status === "failed") {
      await debugScreenshot(page, `performance-stress-${test.info().title}`);
    }
  });
});
