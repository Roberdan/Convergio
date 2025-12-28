/**
 * Research & Knowledge Integration E2E Tests
 * Tests technical architecture, market intelligence, and web research capabilities
 * Scenario 3 from testsAug17.md
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
  validateResearchResponse,
} from "../utils/validation-helpers";
import testData from "../fixtures/test-data.json" with { type: "json" };

test.describe("Research & Knowledge Integration Workflows", () => {
  test.beforeEach(async ({ page }) => {
    await loginTestUser(page);
    await clearConversation(page);
  });

  test("Technical Architecture Consultation with Baccio", async ({ page }) => {
    await navigateToAgent(page, "baccio_tech_architect");

    const archQuery = `Baccio, progetta l'architettura completa per una piattaforma SaaS di analytics enterprise 
    che deve gestire 1M+ utenti simultanei. Include:
    - Architettura microservizi con Docker/Kubernetes
    - Database strategy (SQL + NoSQL + time-series)
    - Caching layers (Redis/CDN)
    - API Gateway e load balancing
    - Security architecture (Auth, encryption, compliance)
    - Monitoring e observability stack
    - Disaster recovery e backup strategy`;

    const startTime = Date.now();

    await sendAgentQuery(page, "baccio_tech_architect", archQuery);

    const response = await getLatestAgentResponse(page, 60000); // Extended for complex architecture
    const responseTime = Date.now() - startTime;

    // Validate technical architecture response
    await expectAIResponse(response, {
      minLength: 400,
      mustHaveStructure: true,
      mustContain: ["microservizi", "kubernetes", "database", "security"],
    });

    // Technical validation
    const content = response.message.toLowerCase();

    // Should include major architectural components
    expect(content).toMatch(/(microservizi|microservice|docker|kubernetes)/);
    expect(content).toMatch(/(database|sql|nosql|redis)/);
    expect(content).toMatch(/(api|gateway|load.balancer)/);
    expect(content).toMatch(/(security|auth|encryption)/);
    expect(content).toMatch(/(monitoring|observability)/);

    // Should include scalability considerations
    expect(content).toMatch(/(scalab|1m|million|utenti|users)/);

    // Should have technical depth
    expect(response.message).toMatch(/[1-9]\.|•|-/); // Structured technical breakdown

    // Performance validation
    expect(responseTime).toBeLessThan(90000);
    expect(response.length).toBeGreaterThan(500);

    console.log(
      `✅ Technical architecture consultation completed in ${responseTime}ms`,
    );
    console.log(`🏗️ Comprehensive system design provided`);
  });

  test("Market Intelligence with Ali + Web Research", async ({ page }) => {
    await navigateToAgent(page, "ali_chief_of_staff");

    const researchQuery = `Ali, conduca una ricerca di mercato completa per il settore "Enterprise Analytics Platforms" nel 2024-2025. 
    Cerca online e analizza:
    - Competitors principali e loro pricing
    - Trend di mercato e crescita prevista  
    - Tecnologie emergenti nel settore
    - Opportunità di differenziazione
    - Best practices e case studies
    Usa fonti web aggiornate e fornisci insights strategici.`;

    const startTime = Date.now();

    await sendAliQuery(page, researchQuery);

    const response = await getLatestAgentResponse(page, 90000); // Extended for web research
    const responseTime = Date.now() - startTime;

    // Validate research response with web integration
    expect(
      validateResearchResponse(response),
      `Research response failed validation: ${response.message.substring(0, 100)}...`,
    ).toBe(true);

    // Should include current market data
    const content = response.message.toLowerCase();
    expect(content).toMatch(/(2024|2025)/);
    expect(content).toMatch(/(analytics|platform|enterprise)/);
    expect(content).toMatch(/(competitor|mercato|market)/);
    expect(content).toMatch(/(trend|crescita|growth)/);

    // Should include web-sourced information
    expect(content).toMatch(/(secondo|based on|fonte|source)/);

    // Business intelligence validation
    await expectBusinessResponse(response, {
      hasStrategicThinking: true,
      hasDataDriven: true,
      hasActionableInsights: true,
    });

    // Performance validation for research
    expect(responseTime).toBeLessThan(120000); // Max 2 minutes for comprehensive research
    expect(response.length).toBeGreaterThan(600);

    console.log(
      `✅ Market intelligence research completed in ${responseTime}ms`,
    );
    console.log(`🔍 Web research and strategic analysis provided`);
  });

  test("Technology Trends Research - AI/ML Stack 2025", async ({ page }) => {
    await navigateToAgent(page, "baccio_tech_architect");

    const techTrendsQuery = `Baccio, ricerca le tecnologie AI/ML più promettenti per il 2025 nel contesto enterprise. 
    Cerca informazioni aggiornate su:
    - Framework e piattaforme AI emergenti
    - MLOps tools e best practices 
    - Edge AI e deployment strategies
    - LLM integration patterns per enterprise
    - Cost optimization per workloads AI
    Fornisci raccomandazioni tecniche concrete per l'implementazione.`;

    const startTime = Date.now();

    await sendAgentQuery(page, "baccio_tech_architect", techTrendsQuery);

    const response = await getLatestAgentResponse(page, 75000);
    const responseTime = Date.now() - startTime;

    // Validate tech research response
    await expectAIResponse(response, {
      minLength: 300,
      mustHaveStructure: true,
      mustContain: ["ai", "ml", "2025", "tecnologie"],
    });

    // Technology-specific validation
    const content = response.message.toLowerCase();

    // Should include AI/ML technologies
    expect(content).toMatch(/(ai|ml|machine learning|artificial intelligence)/);
    expect(content).toMatch(/(framework|platform|tool)/);
    expect(content).toMatch(/(mlops|deployment|edge)/);
    expect(content).toMatch(/(llm|language model)/);

    // Should include implementation guidance
    expect(content).toMatch(/(implement|raccomand|suggest|best practice)/);
    expect(content).toMatch(/(enterprise|cost|optimization)/);

    // Current/future focus
    expect(content).toMatch(/(2025|emerging|nuovo|latest)/);

    // Performance validation
    expect(responseTime).toBeLessThan(90000);
    expect(response.length).toBeGreaterThan(400);

    console.log(`✅ Technology trends research completed in ${responseTime}ms`);
    console.log(`🚀 AI/ML technology recommendations provided`);
  });

  test("Integrated Research Workflow - Ali + Baccio Technology Analysis", async ({
    page,
  }) => {
    await navigateToAgent(page, "ali_chief_of_staff");

    const integratedQuery = `Ali, coordina con Baccio per analizzare completamente le opzioni tecnologiche 
    per una piattaforma enterprise di real-time analytics. 
    
    Ali: fornisci analisi strategica del mercato, positioning competitivo e business case
    Baccio: definisci stack tecnologico ottimale, architettura scalabile e implementation roadmap
    
    Focus su: real-time data processing, ML/AI integration, enterprise security, global scalability.`;

    const startTime = Date.now();

    await sendAliQuery(page, integratedQuery);

    // Wait for coordinated analysis
    const responses = await waitForOrchestration(
      page,
      ["ali", "baccio"],
      120000,
    );
    const totalTime = Date.now() - startTime;

    // Validate coordination success
    expect(responses.length).toBeGreaterThanOrEqual(2);

    // Validate strategic and technical content
    const allContent = responses
      .map((r) => r.message)
      .join(" ")
      .toLowerCase();

    // Should have strategic business content
    const hasStrategicContent =
      /strategic|business|market|competitive|positioning/.test(allContent);

    // Should have technical content
    const hasTechnicalContent =
      /architecture|stack|technology|implementation|scalable/.test(allContent);

    // Should have real-time analytics content
    const hasAnalyticsContent =
      /real.time|analytics|data.processing|ml|ai/.test(allContent);

    expect(hasStrategicContent, "Should include strategic analysis").toBe(true);
    expect(hasTechnicalContent, "Should include technical architecture").toBe(
      true,
    );
    expect(
      hasAnalyticsContent,
      "Should include analytics-specific content",
    ).toBe(true);

    // Validate individual responses
    for (const response of responses) {
      await expectAIResponse(response, { minLength: 200 });
    }

    // Performance validation
    expect(totalTime).toBeLessThan(180000); // Max 3 minutes for integrated analysis

    console.log(`✅ Integrated research workflow completed in ${totalTime}ms`);
    console.log(`🎯 Strategic + Technical analysis coordinated`);
    console.log(
      `📊 Content coverage: Strategic=${hasStrategicContent}, Technical=${hasTechnicalContent}, Analytics=${hasAnalyticsContent}`,
    );
  });

  test("Competitive Intelligence - Real-time Market Analysis", async ({
    page,
  }) => {
    await navigateToAgent(page, "ali_chief_of_staff");

    const competitiveQuery = `Ali, esegui un'analisi competitiva in tempo reale per il mercato "Business Intelligence Platforms". 
    Cerca informazioni aggiornate sui top 5 competitors:
    - Tableau, PowerBI, Looker, Qlik, Sisense
    
    Per ciascuno analizza:
    - Pricing models attuali e cambiamenti recenti
    - Nuove features lanciate nel 2024
    - Customer reviews e feedback
    - Market share e crescita
    - Punti di forza e debolezze
    
    Fornisci insight strategici per il positioning competitivo.`;

    const startTime = Date.now();

    await sendAliQuery(page, competitiveQuery);

    const response = await getLatestAgentResponse(page, 100000); // Extended for comprehensive analysis
    const responseTime = Date.now() - startTime;

    // Validate competitive research
    expect(validateResearchResponse(response)).toBe(true);

    // Should reference major competitors
    const content = response.message.toLowerCase();
    const competitors = [
      "tableau",
      "powerbi",
      "power bi",
      "looker",
      "qlik",
      "sisense",
    ];
    const mentionedCompetitors = competitors.filter((comp) =>
      content.includes(comp),
    );
    expect(mentionedCompetitors.length).toBeGreaterThanOrEqual(3); // At least 3 competitors mentioned

    // Should include competitive analysis elements
    expect(content).toMatch(/(pricing|price|cost)/);
    expect(content).toMatch(/(feature|functionality|capability)/);
    expect(content).toMatch(/(market.share|crescita|growth)/);
    expect(content).toMatch(/(strength|weakness|forte|debolezza)/);

    // Should include strategic insights
    expect(content).toMatch(/(positioning|strategy|recommend|insight)/);
    expect(content).toMatch(/(competitive|advantage|differentiation)/);

    // Current market focus
    expect(content).toMatch(/(2024|recent|latest|nuovo)/);

    // Business validation
    await expectBusinessResponse(response, {
      hasStrategicThinking: true,
      hasDataDriven: true,
      hasActionableInsights: true,
    });

    // Performance validation
    expect(responseTime).toBeLessThan(150000); // Max 2.5 minutes for comprehensive competitive analysis
    expect(response.length).toBeGreaterThan(700);

    console.log(`✅ Competitive intelligence completed in ${responseTime}ms`);
    console.log(`🎯 ${mentionedCompetitors.length} competitors analyzed`);
    console.log(`📈 Strategic positioning insights provided`);
  });

  test("Knowledge Integration - Cross-Domain Research", async ({ page }) => {
    // Test ability to integrate knowledge across business, technical, and market domains
    await navigateToAgent(page, "ali_chief_of_staff");

    const crossDomainQuery = `Ali, integra conoscenze da diversi domini per rispondere a questa sfida:
    
    "Come possiamo creare una piattaforma di analytics che sia tecnicamente superiore ai competitor, 
    economicamente sostenibile, e strategicamente posizionata per dominare il mercato enterprise nei prossimi 3 anni?"
    
    Integra:
    - Analisi tecnica delle soluzioni più avanzate
    - Modelli di business vincenti nel settore
    - Trend di mercato e opportunità future
    - Strategia di go-to-market differenziata
    
    Fornisci una roadmap integrata business + tech + market.`;

    const startTime = Date.now();

    await sendAliQuery(page, crossDomainQuery);

    const response = await getLatestAgentResponse(page, 120000);
    const responseTime = Date.now() - startTime;

    // Validate comprehensive cross-domain response
    await expectBusinessResponse(response, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
      hasDataDriven: true,
      hasTimeframes: true,
      hasRisksConsideration: true,
    });

    // Should integrate multiple domains
    const content = response.message.toLowerCase();

    // Technical domain
    const hasTechnical =
      /technical|technology|architecture|platform|scalab/.test(content);

    // Business domain
    const hasBusiness = /business|model|revenue|cost|profit|economic/.test(
      content,
    );

    // Market domain
    const hasMarket = /market|competitor|customer|enterprise|positioning/.test(
      content,
    );

    // Strategic domain
    const hasStrategy = /strategy|strategic|roadmap|plan|vision|goal/.test(
      content,
    );

    // Should integrate at least 3 of 4 domains
    const domainCoverage = [
      hasTechnical,
      hasBusiness,
      hasMarket,
      hasStrategy,
    ].filter(Boolean).length;
    expect(domainCoverage).toBeGreaterThanOrEqual(3);

    // Should include future-oriented thinking
    expect(content).toMatch(/(3 anni|future|prossimi|trend|evolution)/);

    // Should include implementation roadmap
    expect(content).toMatch(/(roadmap|step|fase|implementation|execute)/);

    // Performance validation for complex integration
    expect(responseTime).toBeLessThan(180000); // Max 3 minutes for cross-domain integration
    expect(response.length).toBeGreaterThan(800);

    console.log(
      `✅ Cross-domain knowledge integration completed in ${responseTime}ms`,
    );
    console.log(
      `🧠 Domain coverage: Technical=${hasTechnical}, Business=${hasBusiness}, Market=${hasMarket}, Strategy=${hasStrategy}`,
    );
  });

  test.afterEach(async ({ page }) => {
    if (test.info().status === "failed") {
      await debugScreenshot(page, `research-workflows-${test.info().title}`);
    }
  });
});
