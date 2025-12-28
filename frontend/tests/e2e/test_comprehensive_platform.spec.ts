/**
 * Comprehensive Platform E2E Tests
 * Tests the complete Convergio vision: "a team you direct, not software you use"
 * Based on AgenticManifesto/WhatIsConvergio.md and the 48-agent ecosystem
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

test.describe("Comprehensive Platform Features - 48 Agent Ecosystem", () => {
  test.beforeEach(async ({ page }) => {
    await loginTestUser(page);
    await clearConversation(page);
  });

  test("CEO Experience: Managing Complex Organization through AI Team", async ({
    page,
  }) => {
    // Test the core vision: "a single person can manage an entire complex organization"
    await navigateToAgent(page, "ali_chief_of_staff");

    const ceoScenario = `Ali, come CEO di una startup tecnologica, ho bisogno di gestire completamente 
    il lancio del nostro nuovo prodotto SaaS "Analytics Pro". 
    
    Coordina il tuo team per fornirmi:
    - Strategia completa di lancio (Antonio/Matteo per strategy)
    - Piano finanziario e budget (Amy CFO per financial planning)
    - Architettura tecnica e scalabilità (Baccio/Dan per tech architecture)
    - Piano di marketing e positioning (Sofia per marketing)
    - Roadmap di sviluppo (Marcus/Davide per project management)
    - Analisi dei rischi (Luca per security, Elena per legal)
    
    Voglio una soluzione integrata e coordinata, non risposte separate.`;

    const startTime = Date.now();

    await sendAliQuery(page, ceoScenario);

    // Extended timeout for complex organizational coordination
    const responses = await waitForOrchestration(page, ["ali"], 180000);
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const aliResponse = responses[0];
    const content = aliResponse.message.toLowerCase();

    // Should demonstrate comprehensive CEO-level coordination
    expect(content).toMatch(
      /(strateg|marketing|financial|technical|roadmap|risk).*strateg|marketing|financial|technical|roadmap|risk/,
    ); // Multiple domains
    expect(content).toMatch(/(team|coordinat|orchestrat|integrat)/); // Team coordination
    expect(content).toMatch(/(ceo|executive|leadership|organization)/); // CEO-level thinking

    // Should reference multiple specialized areas
    const hasStrategy = /strateg|vision|positioning|market.entry/.test(content);
    const hasFinancial = /budget|financial|roi|cost|revenue/.test(content);
    const hasTechnical = /architect|technical|scalab|infrastructure/.test(
      content,
    );
    const hasMarketing = /marketing|brand|launch|messaging/.test(content);
    const hasProject = /roadmap|timeline|milestone|project/.test(content);

    const domainsCovered = [
      hasStrategy,
      hasFinancial,
      hasTechnical,
      hasMarketing,
      hasProject,
    ].filter(Boolean).length;
    expect(domainsCovered).toBeGreaterThanOrEqual(4); // Should cover most domains

    // Business validation for CEO-level response
    await expectBusinessResponse(aliResponse, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
      hasTimeframes: true,
      hasRisksConsideration: true,
    });

    expect(totalTime).toBeLessThan(240000); // Max 4 minutes for comprehensive coordination
    expect(aliResponse.length).toBeGreaterThan(600);

    console.log(
      `✅ CEO-level organizational management completed in ${totalTime}ms`,
    );
    console.log(
      `🎯 Domains covered: Strategy=${hasStrategy}, Finance=${hasFinancial}, Tech=${hasTechnical}, Marketing=${hasMarketing}, Project=${hasProject}`,
    );
  });

  test("Startup Founder Experience: Complete Business Creation Flow", async ({
    page,
  }) => {
    // Test the "democratization of entrepreneurship" vision
    await navigateToAgent(page, "ali_chief_of_staff");

    const startupScenario = `Ali, sono un founder di una startup fitness tech. Ho un'idea per un'app 
    che combina AI personal training con community features. 
    
    Coordina Sam (Startup Expert), Michael (VC), Wiz (Investor), e il tuo team per aiutarmi a:
    
    1. Validare e strutturare l'idea di business (Sam Startup Expert)
    2. Creare un pitch deck per investitori (Michael VC perspective)
    3. Sviluppare proiezioni finanziarie (Amy CFO + Wiz Investor)
    4. Definire la strategia di go-to-market (Sofia Marketing + Antonio Strategy)
    5. Pianificare l'MVP tecnico (Baccio Tech Architect + Davide PM)
    
    Voglio uscire da questa conversazione con tutto quello che serve per iniziare.`;

    const startTime = Date.now();

    await sendAliQuery(page, startupScenario);

    const responses = await waitForOrchestration(page, ["ali"], 180000);
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const aliResponse = responses[0];
    const content = aliResponse.message.toLowerCase();

    // Should demonstrate startup ecosystem support
    expect(content).toMatch(/(startup|founder|mvp|pitch|investor)/);
    expect(content).toMatch(
      /(business.model|go.to.market|revenue|market.validation)/,
    );
    expect(content).toMatch(/(fitness|tech|ai|personal.training|community)/); // Industry specificity

    // Should include key startup elements
    const hasBusinessValidation =
      /validat|business.model|market.fit|customer/.test(content);
    const hasPitchElements = /pitch|investor|deck|funding|valuation/.test(
      content,
    );
    const hasFinancialProjections =
      /financial|projection|revenue|cost|roi/.test(content);
    const hasMarketStrategy = /market|go.to.market|customer|acquisition/.test(
      content,
    );
    const hasTechnicalPlan = /mvp|technical|architect|development/.test(
      content,
    );

    const startupElements = [
      hasBusinessValidation,
      hasPitchElements,
      hasFinancialProjections,
      hasMarketStrategy,
      hasTechnicalPlan,
    ].filter(Boolean).length;
    expect(startupElements).toBeGreaterThanOrEqual(4);

    // Should be actionable for founders
    await expectBusinessResponse(aliResponse, {
      hasActionableInsights: true,
      hasDataDriven: true,
      hasTimeframes: true,
    });

    expect(totalTime).toBeLessThan(240000);
    expect(aliResponse.length).toBeGreaterThan(500);

    console.log(`✅ Startup founder support completed in ${totalTime}ms`);
    console.log(
      `🚀 Startup elements: Validation=${hasBusinessValidation}, Pitch=${hasPitchElements}, Finance=${hasFinancialProjections}, Market=${hasMarketStrategy}, Tech=${hasTechnicalPlan}`,
    );
  });

  test("Technology Excellence: Full-Stack Technical Solution", async ({
    page,
  }) => {
    // Test the deep technical capabilities of the platform
    await navigateToAgent(page, "ali_chief_of_staff");

    const techScenario = `Ali, coordina Dan (Engineering GM), Baccio (Tech Architect), Marco (DevOps), 
    Luca (Security), e Thor (QA) per progettare completamente un sistema enterprise-grade.
    
    Requisiti: Piattaforma di analytics real-time per Fortune 500 company
    - 10M+ eventi al giorno, latenza <100ms
    - Multi-region deployment con disaster recovery
    - Enterprise security e compliance (SOC2, GDPR)
    - Auto-scaling e cost optimization
    - CI/CD completo e testing automation
    
    Voglio una soluzione tecnica completa e production-ready.`;

    const startTime = Date.now();

    await sendAliQuery(page, techScenario);

    const responses = await waitForOrchestration(page, ["ali"], 180000);
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const aliResponse = responses[0];
    const content = aliResponse.message.toLowerCase();

    // Should demonstrate enterprise technical depth
    expect(content).toMatch(/(architect|technical|enterprise|production)/);
    expect(content).toMatch(/(scalab|performance|security|compliance)/);
    expect(content).toMatch(/(real.time|analytics|10m|latency)/); // Requirements specificity

    // Should include comprehensive technical areas
    const hasArchitecture = /architect|microservice|system.design|scalab/.test(
      content,
    );
    const hasDevOps = /devops|ci.cd|deploy|pipeline|infrastructure/.test(
      content,
    );
    const hasSecurity = /security|compliance|encryption|soc2|gdpr/.test(
      content,
    );
    const hasPerformance = /performance|latency|optimization|auto.scal/.test(
      content,
    );
    const hasQuality = /quality|test|qa|automation|monitoring/.test(content);

    const technicalAreas = [
      hasArchitecture,
      hasDevOps,
      hasSecurity,
      hasPerformance,
      hasQuality,
    ].filter(Boolean).length;
    expect(technicalAreas).toBeGreaterThanOrEqual(4);

    // Should be enterprise-grade
    expect(content).toMatch(
      /(enterprise|production|fortune.500|mission.critical)/,
    );
    expect(content).toMatch(/(disaster.recovery|high.availability|redundancy)/);

    await expectAIResponse(aliResponse, {
      minLength: 500,
      mustHaveStructure: true,
    });

    expect(totalTime).toBeLessThan(240000);

    console.log(
      `✅ Technology excellence demonstration completed in ${totalTime}ms`,
    );
    console.log(
      `🔧 Technical areas: Architecture=${hasArchitecture}, DevOps=${hasDevOps}, Security=${hasSecurity}, Performance=${hasPerformance}, QA=${hasQuality}`,
    );
  });

  test("Data-Driven Decision Making: Complete Analytics Ecosystem", async ({
    page,
  }) => {
    // Test the data and analytics capabilities
    await navigateToAgent(page, "ali_chief_of_staff");

    const dataScenario = `Ali, coordina Ava (Analytics Virtuoso), Angela (Data Analyst), 
    Omri (Data Scientist), Ethan IC6 (Senior Data Analyst), e Diana (Dashboard Expert) 
    per una soluzione completa di business intelligence.
    
    Obiettivo: Trasformare i dati aziendali in insights strategici
    - Analisi predittive per revenue forecasting
    - Customer churn prevention con ML
    - Performance dashboard real-time per C-level
    - Competitive intelligence e market analysis
    - ROI optimization per marketing campaigns
    
    Voglio diventare una truly data-driven organization.`;

    const startTime = Date.now();

    await sendAliQuery(page, dataScenario);

    const responses = await waitForOrchestration(page, ["ali"], 150000);
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const aliResponse = responses[0];
    const content = aliResponse.message.toLowerCase();

    // Should demonstrate comprehensive data capabilities
    expect(content).toMatch(/(data|analytics|intelligence|insight)/);
    expect(content).toMatch(/(predictive|machine.learning|ml|forecast)/);
    expect(content).toMatch(/(dashboard|visualization|real.time)/);

    // Should include key data areas
    const hasPredictiveAnalytics =
      /predictive|forecast|machine.learning|ml|model/.test(content);
    const hasCustomerInsights = /customer|churn|retention|lifetime.value/.test(
      content,
    );
    const hasDashboards = /dashboard|visualization|real.time|kpi/.test(content);
    const hasCompetitiveIntel = /competitive|market|intelligence|analysis/.test(
      content,
    );
    const hasROIOptimization = /roi|optimization|marketing|campaign/.test(
      content,
    );

    const dataCapabilities = [
      hasPredictiveAnalytics,
      hasCustomerInsights,
      hasDashboards,
      hasCompetitiveIntel,
      hasROIOptimization,
    ].filter(Boolean).length;
    expect(dataCapabilities).toBeGreaterThanOrEqual(3);

    // Should be data-driven and strategic
    await expectBusinessResponse(aliResponse, {
      hasDataDriven: true,
      hasStrategicThinking: true,
      hasActionableInsights: true,
    });

    expect(totalTime).toBeLessThan(200000);

    console.log(
      `✅ Data-driven analytics ecosystem completed in ${totalTime}ms`,
    );
    console.log(
      `📊 Data capabilities: Predictive=${hasPredictiveAnalytics}, Customer=${hasCustomerInsights}, Dashboards=${hasDashboards}, Competitive=${hasCompetitiveIntel}, ROI=${hasROIOptimization}`,
    );
  });

  test("Human-Centric Culture: People and Organization Development", async ({
    page,
  }) => {
    // Test the human resources and culture capabilities
    await navigateToAgent(page, "ali_chief_of_staff");

    const cultureScenario = `Ali, coordina Giulia (HR Talent), Coach (Team Coach), 
    Behice (Cultural Coach), Jenny (Accessibility Champion), e Dave (Change Management) 
    per trasformare la nostra cultura aziendale.
    
    Sfida: Siamo cresciuti da 15 a 150 persone in 18 mesi. Dobbiamo:
    - Mantenere la cultura startup innovativa
    - Implementare processi scalabili ma non burocratici  
    - Creare inclusivity e accessibility by design
    - Gestire il change management della crescita
    - Attrarre e trattenere top talent in competizione con FAANG
    
    Voglio un'organizzazione che scala mantenendo i valori umani.`;

    const startTime = Date.now();

    await sendAliQuery(page, cultureScenario);

    const responses = await waitForOrchestration(page, ["ali"], 150000);
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const aliResponse = responses[0];
    const content = aliResponse.message.toLowerCase();

    // Should demonstrate human-centric approach
    expect(content).toMatch(/(cultur|human|people|talent|team)/);
    expect(content).toMatch(/(growth|scaling|startup|innovation)/);
    expect(content).toMatch(/(inclusiv|accessibility|diversity)/);

    // Should include key people areas
    const hasCultureManagement =
      /cultur|values|startup|innovation|maintain/.test(content);
    const hasTalentStrategy = /talent|hr|recruit|retain|faang|attract/.test(
      content,
    );
    const hasInclusivity = /inclusiv|accessibility|diversity|inclusive/.test(
      content,
    );
    const hasChangeManagement = /change|growth|scaling|transition|process/.test(
      content,
    );
    const hasTeamDevelopment = /team|coach|development|leadership/.test(
      content,
    );

    const peopleAspects = [
      hasCultureManagement,
      hasTalentStrategy,
      hasInclusivity,
      hasChangeManagement,
      hasTeamDevelopment,
    ].filter(Boolean).length;
    expect(peopleAspects).toBeGreaterThanOrEqual(3);

    // Should balance scaling with human values
    expect(content).toMatch(
      /(scale|scalab|grow).*human|human.*scale|scalab|grow/,
    );
    expect(content).toMatch(
      /(process|structure).*values|values.*process|structure/,
    );

    await expectBusinessResponse(aliResponse, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
    });

    expect(totalTime).toBeLessThan(200000);

    console.log(
      `✅ Human-centric culture development completed in ${totalTime}ms`,
    );
    console.log(
      `👥 People aspects: Culture=${hasCultureManagement}, Talent=${hasTalentStrategy}, Inclusion=${hasInclusivity}, Change=${hasChangeManagement}, Team=${hasTeamDevelopment}`,
    );
  });

  test('Transparency and "Why" Explanations - Core Value Test', async ({
    page,
  }) => {
    // Test the core value: "You can always ask an agent 'why' it made a certain decision"
    await navigateToAgent(page, "ali_chief_of_staff");

    const decisionQuery = `Ali, raccomanda la migliore strategia di pricing per il nostro SaaS B2B. 
    Considera: competitors a $99/mese, nostra value proposition superiore, target enterprise.`;

    await sendAliQuery(page, decisionQuery);

    const initialResponse = await getLatestAgentResponse(page, 60000);
    expect(initialResponse.message).toBeTruthy();

    // Now ask "why" - test transparency
    const whyQuery = `Ali, perché hai raccomandato quella specifica strategia di pricing? 
    Spiegami il tuo ragionamento step-by-step.`;

    await sendAliQuery(page, whyQuery);

    const explanationResponse = await getLatestAgentResponse(page, 60000);
    const explanationContent = explanationResponse.message.toLowerCase();

    // Should provide clear reasoning
    expect(explanationContent).toMatch(/(perché|because|ragion|reason|motiv)/);
    expect(explanationContent).toMatch(/(consider|analiz|evaluat|pensato)/);
    expect(explanationContent).toMatch(/(step|fase|processo|approach)/);

    // Should reference decision factors
    expect(explanationContent).toMatch(
      /(competitor|value.proposition|enterprise|target)/,
    );
    expect(explanationContent).toMatch(/(pricing|strategy|decision|recommend)/);

    // Should be educational and transparent
    expect(explanationContent).toMatch(
      /(first|second|third|poi|inoltre|inoltre)/,
    ); // Structured explanation

    await expectAIResponse(explanationResponse, {
      minLength: 200,
      mustHaveStructure: true,
    });

    console.log(`✅ Transparency and "why" explanation test passed`);
    console.log(`🔍 Agent provided clear decision reasoning`);
  });

  test("Human Final Say - Decision Authority Test", async ({ page }) => {
    // Test the core value: "Humans always have the final say"
    await navigateToAgent(page, "ali_chief_of_staff");

    const proposalQuery = `Ali, proponi una strategia di acquisizione per crescere velocemente. 
    Budget disponibile: $2M. Settore: fintech B2B.`;

    await sendAliQuery(page, proposalQuery);

    const proposalResponse = await getLatestAgentResponse(page, 60000);
    expect(proposalResponse.message).toBeTruthy();

    // Reject the proposal and ask for alternatives
    const rejectionQuery = `Ali, non sono convinto della tua proposta. È troppo rischiosa per noi ora. 
    Proponi 3 alternative più conservative ma comunque di crescita.`;

    await sendAliQuery(page, rejectionQuery);

    const alternativesResponse = await getLatestAgentResponse(page, 60000);
    const alternativesContent = alternativesResponse.message.toLowerCase();

    // Should respect human decision and provide alternatives
    expect(alternativesContent).toMatch(
      /(understand|capisco|rispetto|comprendo)/,
    );
    expect(alternativesContent).toMatch(/(alternat|option|different|invece)/);
    expect(alternativesContent).toMatch(
      /(conservativ|risk.averse|safer|prudent)/,
    );

    // Should provide multiple options
    expect(alternativesContent).toMatch(
      /(1\.|first|primo|alternative.1|opzione.1)/,
    );
    expect(alternativesContent).toMatch(
      /(2\.|second|secondo|alternative.2|opzione.2)/,
    );
    expect(alternativesContent).toMatch(
      /(3\.|third|terzo|alternative.3|opzione.3)/,
    );

    // Should acknowledge human authority
    expect(alternativesContent).toMatch(
      /(your.decision|your.call|you.decide|your.choice|decision|decisione)/,
    );

    await expectAIResponse(alternativesResponse, {
      minLength: 300,
      mustHaveStructure: true,
    });

    console.log(`✅ Human final say authority test passed`);
    console.log(`👤 Agent respected human decision and provided alternatives`);
  });

  test("Accessibility and Inclusion - Platform Values Test", async ({
    page,
  }) => {
    // Test the accessibility and inclusion features
    await navigateToAgent(page, "jenny_inclusive_accessibility_champion");

    const accessibilityQuery = `Jenny, voglio rendere la nostra piattaforma SaaS completamente accessibile. 
    Attualmente abbiamo problemi con screen readers, contrasti colori, e navigazione keyboard.
    
    Fornisci un piano completo per WCAG 2.1 AA compliance e inclusive design.`;

    const startTime = Date.now();

    await sendAgentQuery(
      page,
      "jenny_inclusive_accessibility_champion",
      accessibilityQuery,
    );

    const response = await getLatestAgentResponse(page, 60000);
    const responseTime = Date.now() - startTime;

    // Validate accessibility expertise
    await expectAIResponse(response, {
      minLength: 300,
      mustHaveStructure: true,
      mustContain: ["accessibility", "wcag", "inclusive"],
    });

    // Accessibility-specific validation
    const content = response.message.toLowerCase();

    // Should include WCAG compliance
    expect(content).toMatch(/(wcag|accessibility|a11y|compliance)/);
    expect(content).toMatch(/(screen.reader|keyboard|color.contrast)/);
    expect(content).toMatch(/(inclusive|universal.design|disability)/);

    // Should include practical guidance
    expect(content).toMatch(/(aria|semantic|focus|navigation)/);
    expect(content).toMatch(/(test|audit|validation|compliance)/);

    // Should be comprehensive
    expect(content).toMatch(/(plan|strategy|implement|guidelines)/);

    // Performance validation
    expect(responseTime).toBeLessThan(90000);
    expect(response.length).toBeGreaterThan(400);

    console.log(
      `✅ Accessibility and inclusion test completed in ${responseTime}ms`,
    );
    console.log(`♿ Platform accessibility validation successful`);
  });

  test.afterEach(async ({ page }) => {
    if (test.info().status === "failed") {
      await debugScreenshot(
        page,
        `comprehensive-platform-${test.info().title}`,
      );
    }
  });
});
