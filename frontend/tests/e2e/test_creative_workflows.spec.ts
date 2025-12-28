/**
 * Creative & Design Workflows E2E Tests
 * Tests UX/UI design and storytelling capabilities
 * Scenario 4 from testsAug17.md
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

test.describe("Creative & Design Workflows", () => {
  test.beforeEach(async ({ page }) => {
    await loginTestUser(page);
    await clearConversation(page);
  });

  test("UX/UI Design Process with Sara", async ({ page }) => {
    await navigateToAgent(page, "sara_ux_ui_designer");

    const designQuery = `Sara, progetta l'interfaccia completa per una dashboard executive di analytics enterprise. 
    
    Requisiti:
    - Utenti: C-level executives, managers senior
    - Obiettivo: Decisioni strategiche rapide basate su dati
    - Dispositivi: Desktop primario, tablet/mobile per consultazione
    - Dati: KPI business, analytics real-time, trend forecasting
    
    Fornisci:
    - Information architecture e user flow
    - Wireframes dettagliati per schermate principali  
    - Design system (colori, typography, componenti)
    - Principi di usabilità e accessibility
    - Mobile-responsive considerations`;

    const startTime = Date.now();

    await sendAgentQuery(page, "sara_ux_ui_designer", designQuery);

    const response = await getLatestAgentResponse(page, 60000);
    const responseTime = Date.now() - startTime;

    // Validate UX/UI design response
    await expectAIResponse(response, {
      minLength: 400,
      mustHaveStructure: true,
      mustContain: ["ux", "ui", "design", "dashboard"],
    });

    // Design-specific validation
    const content = response.message.toLowerCase();

    // Should include design methodology
    expect(content).toMatch(
      /(user.flow|wireframe|user.journey|information.architecture)/,
    );
    expect(content).toMatch(/(design.system|component|typography|color)/);
    expect(content).toMatch(/(usability|accessibility|user.experience)/);

    // Should address requirements
    expect(content).toMatch(/(executive|dashboard|kpi|analytics)/);
    expect(content).toMatch(/(mobile|responsive|tablet|desktop)/);

    // Should include practical design guidance
    expect(content).toMatch(/(layout|navigation|visual|interface)/);
    expect(content).toMatch(/(hierarchy|priority|focus|attention)/);

    // Business context understanding
    await expectBusinessResponse(response, {
      hasActionableInsights: true,
      hasDataDriven: true,
    });

    // Performance validation
    expect(responseTime).toBeLessThan(90000);
    expect(response.length).toBeGreaterThan(500);

    console.log(`✅ UX/UI design consultation completed in ${responseTime}ms`);
    console.log(`🎨 Comprehensive design system provided`);
  });

  test("Content & Storytelling with Riccardo", async ({ page }) => {
    await navigateToAgent(page, "riccardo_storyteller");

    const storyQuery = `Riccardo, crea la narrative completa per il lancio della nostra nuova piattaforma di analytics AI enterprise.
    
    Contesto prodotto:
    - Nome: "InsightFlow AI"
    - Target: Enterprise Fortune 500
    - USP: Analytics predittive con AI conversazionale
    - Differenziatori: Real-time processing, natural language queries, automated insights
    
    Crea:
    - Brand story e positioning narrative
    - Messaggi chiave per audience diverse (CTO, CEO, Data teams)
    - Content strategy per go-to-market
    - Storytelling per demo e presentazioni
    - Social media narrative e thought leadership
    - Case study framework per customer success`;

    const startTime = Date.now();

    await sendAgentQuery(page, "riccardo_storyteller", storyQuery);

    const response = await getLatestAgentResponse(page, 50000);
    const responseTime = Date.now() - startTime;

    // Validate storytelling response
    await expectAIResponse(response, {
      minLength: 350,
      mustHaveStructure: true,
      mustContain: ["story", "narrative", "messaging", "brand"],
    });

    // Storytelling-specific validation
    const content = response.message.toLowerCase();

    // Should include storytelling elements
    expect(content).toMatch(/(story|narrative|message|brand|positioning)/);
    expect(content).toMatch(/(audience|target|customer|stakeholder)/);
    expect(content).toMatch(
      /(value.proposition|benefit|advantage|differentiator)/,
    );

    // Should reference the product
    expect(content).toMatch(/(insightflow|analytics|ai|enterprise)/);
    expect(content).toMatch(/(predictive|real.time|natural.language)/);

    // Should include marketing strategy
    expect(content).toMatch(/(go.to.market|content|demo|presentation)/);
    expect(content).toMatch(/(social.media|thought.leadership|case.study)/);

    // Should address different audiences
    expect(content).toMatch(/(cto|ceo|data.team|c.level|executive)/);

    // Business validation for marketing content
    await expectBusinessResponse(response, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
    });

    // Performance validation
    expect(responseTime).toBeLessThan(70000);
    expect(response.length).toBeGreaterThan(400);

    console.log(
      `✅ Content & storytelling strategy completed in ${responseTime}ms`,
    );
    console.log(`📖 Brand narrative and marketing strategy provided`);
  });

  test("Integrated Creative Workflow - Ali + Sara + Riccardo Product Launch", async ({
    page,
  }) => {
    await navigateToAgent(page, "ali_chief_of_staff");

    const scenario = testData.business_scenarios.product_launch;
    const creativeQuery = `Ali, coordina Sara (UX/UI Designer) e Riccardo (Storyteller) per creare 
    l'esperienza completa di lancio per ${scenario.title}.
    
    Obiettivo: Creare una presentazione di lancio che combini:
    - Ali: Strategia di positioning e go-to-market
    - Sara: Design dell'esperienza di presentazione e demo UI
    - Riccardo: Narrative coinvolgente e messaging efficace
    
    Contesto: ${scenario.description}
    Target: ${scenario.context.target_audience}
    Timeline: ${scenario.context.timeline}
    
    Coordinate per creare una presentazione integrata che convinca il C-level.`;

    const startTime = Date.now();

    await sendAliQuery(page, creativeQuery);

    // Wait for creative collaboration
    const responses = await waitForOrchestration(
      page,
      ["ali", "sara", "riccardo"],
      150000,
    );
    const totalTime = Date.now() - startTime;

    // Validate creative collaboration
    expect(responses.length).toBeGreaterThanOrEqual(2);

    // Validate content integration
    const allContent = responses
      .map((r) => r.message)
      .join(" ")
      .toLowerCase();

    // Should have strategic content (Ali)
    const hasStrategy =
      /strategy|strategic|positioning|go.to.market|market/.test(allContent);

    // Should have design content (Sara)
    const hasDesign =
      /design|interface|user|experience|visual|presentation/.test(allContent);

    // Should have storytelling content (Riccardo)
    const hasStory = /story|narrative|message|brand|audience|compelling/.test(
      allContent,
    );

    // Should reference the product launch context
    const hasProductContext =
      /analytics|platform|enterprise|c.level|launch/.test(allContent);

    expect(hasStrategy, "Should include strategic thinking").toBe(true);
    expect(
      hasDesign || hasStory,
      "Should include design or storytelling content",
    ).toBe(true);
    expect(hasProductContext, "Should reference product launch context").toBe(
      true,
    );

    // Validate individual creative responses
    for (const response of responses) {
      await expectAIResponse(response, {
        minLength: 150,
        mustHaveStructure: true,
      });
    }

    // Performance validation for creative coordination
    expect(totalTime).toBeLessThan(240000); // Max 4 minutes for creative collaboration

    console.log(`✅ Integrated creative workflow completed in ${totalTime}ms`);
    console.log(`🎨 Creative collaboration coordinated successfully`);
    console.log(
      `📊 Content coverage: Strategy=${hasStrategy}, Design=${hasDesign}, Story=${hasStory}`,
    );
  });

  test("User Experience Optimization - Ali + Sara Conversion Funnel", async ({
    page,
  }) => {
    await navigateToAgent(page, "ali_chief_of_staff");

    const uxOptimizationQuery = `Ali, collabora con Sara per ottimizzare il conversion funnel della nostra piattaforma SaaS.
    
    Scenario: 
    - Landing page conversion: attualmente 2.1%, target 4.5%
    - Trial-to-paid conversion: attualmente 18%, target 35%
    - Feature adoption: Core features usate solo dal 45% degli utenti
    
    Ali: Analizza bottlenecks business e strategie di ottimizzazione
    Sara: Proponi miglioramenti UX/UI per ridurre friction e aumentare engagement
    
    Focus su: onboarding experience, value demonstration, feature discovery, decision triggers.`;

    const startTime = Date.now();

    await sendAliQuery(page, uxOptimizationQuery);

    // Wait for UX optimization collaboration
    const responses = await waitForOrchestration(page, ["ali", "sara"], 120000);
    const totalTime = Date.now() - startTime;

    // Validate optimization analysis
    expect(responses.length).toBeGreaterThanOrEqual(2);

    const allContent = responses
      .map((r) => r.message)
      .join(" ")
      .toLowerCase();

    // Should address conversion optimization
    expect(allContent).toMatch(/(conversion|funnel|optimization|improvement)/);
    expect(allContent).toMatch(/(onboarding|trial|feature.adoption)/);

    // Should include specific metrics/targets
    expect(allContent).toMatch(/(2\.1|4\.5|18|35|45)%?/); // Reference provided metrics

    // Should include actionable improvements
    expect(allContent).toMatch(/(improve|optimize|reduce|increase|enhance)/);
    expect(allContent).toMatch(/(friction|engagement|value|decision)/);

    // Should combine business + UX perspectives
    const hasBusiness = /business|strategy|bottleneck|revenue|customer/.test(
      allContent,
    );
    const hasUX = /ux|ui|user|experience|interface|design/.test(allContent);
    expect(
      hasBusiness && hasUX,
      "Should combine business and UX perspectives",
    ).toBe(true);

    // Performance validation
    expect(totalTime).toBeLessThan(180000);

    console.log(`✅ UX optimization workflow completed in ${totalTime}ms`);
    console.log(`📈 Conversion funnel optimization strategies provided`);
  });

  test("Brand Identity Creation - Riccardo Comprehensive Branding", async ({
    page,
  }) => {
    await navigateToAgent(page, "riccardo_storyteller");

    const brandQuery = `Riccardo, sviluppa l'identità di brand completa per una startup innovativa nel settore AI consulting.
    
    Brief:
    - Nome: "Nexus AI Consulting"  
    - Mission: Democratizzare l'AI per le aziende tradizionali
    - Valori: Innovation, Trust, Transformation, Excellence
    - Personalità: Esperta ma accessibile, visionaria ma pragmatica
    - Differenziatori: Approccio human-centric, implementazione rapida, ROI garantito
    
    Sviluppa:
    - Brand manifesto e vision statement
    - Tone of voice e guidelines comunicazione
    - Messaggi core per diversi touchpoints
    - Storytelling per founder story e company narrative
    - Content pillars per thought leadership
    - Brand positioning vs competitor principali`;

    const startTime = Date.now();

    await sendAgentQuery(page, "riccardo_storyteller", brandQuery);

    const response = await getLatestAgentResponse(page, 60000);
    const responseTime = Date.now() - startTime;

    // Validate comprehensive branding response
    await expectAIResponse(response, {
      minLength: 500,
      mustHaveStructure: true,
      mustContain: ["brand", "identity", "nexus", "ai consulting"],
    });

    // Brand-specific validation
    const content = response.message.toLowerCase();

    // Should include brand strategy elements
    expect(content).toMatch(/(brand|identity|manifesto|vision|mission)/);
    expect(content).toMatch(/(tone.of.voice|communication|messaging)/);
    expect(content).toMatch(/(positioning|differentiation|competitor)/);

    // Should reference the company details
    expect(content).toMatch(/(nexus|ai.consulting|democratize)/);
    expect(content).toMatch(/(innovation|trust|transformation|excellence)/);
    expect(content).toMatch(/(human.centric|roi|implementation)/);

    // Should include practical brand guidance
    expect(content).toMatch(/(touchpoint|content|thought.leadership)/);
    expect(content).toMatch(/(founder|story|narrative)/);
    expect(content).toMatch(/(accessible|pragmatic|visionaria)/);

    // Should demonstrate brand personality
    expect(content).toMatch(/(esperta|accessibile|visionaria|pragmatica)/);

    // Business validation for brand strategy
    await expectBusinessResponse(response, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
    });

    // Performance validation
    expect(responseTime).toBeLessThan(90000);
    expect(response.length).toBeGreaterThan(600);

    console.log(`✅ Brand identity creation completed in ${responseTime}ms`);
    console.log(`🌟 Comprehensive brand strategy developed`);
  });

  test("Creative Problem Solving - Design Thinking Workshop", async ({
    page,
  }) => {
    await navigateToAgent(page, "sara_ux_ui_designer");

    const designThinkingQuery = `Sara, facilita un design thinking workshop virtuale per risolvere questa sfida:
    
    "Come possiamo rendere l'analytics enterprise più intuitiva e accessibile per manager non-tecnici?"
    
    Struttura il workshop con:
    - Empathy phase: Definisci user personas e pain points
    - Define phase: Articola il problema core e opportunità
    - Ideate phase: Brainstorming di soluzioni creative
    - Prototype phase: Concept di soluzioni prioritarie
    - Test phase: Criteri di validazione e metriche di successo
    
    Includi metodologie, tool, e deliverable per ogni fase.`;

    const startTime = Date.now();

    await sendAgentQuery(page, "sara_ux_ui_designer", designThinkingQuery);

    const response = await getLatestAgentResponse(page, 70000);
    const responseTime = Date.now() - startTime;

    // Validate design thinking methodology
    await expectAIResponse(response, {
      minLength: 400,
      mustHaveStructure: true,
      mustContain: ["design thinking", "workshop", "empathy", "ideate"],
    });

    // Design thinking validation
    const content = response.message.toLowerCase();

    // Should include all design thinking phases
    expect(content).toMatch(/(empathy|empathize)/);
    expect(content).toMatch(/(define|problem)/);
    expect(content).toMatch(/(ideate|brainstorm|idea)/);
    expect(content).toMatch(/(prototype|concept)/);
    expect(content).toMatch(/(test|validate|validation)/);

    // Should include methodology details
    expect(content).toMatch(/(persona|user|pain.point)/);
    expect(content).toMatch(/(methodology|tool|deliverable)/);
    expect(content).toMatch(/(criteria|metric|success)/);

    // Should address the specific challenge
    expect(content).toMatch(/(analytics|enterprise|manager|non.technical)/);
    expect(content).toMatch(/(intuitive|accessible|user.friendly)/);

    // Should include practical workshop guidance
    expect(content).toMatch(/(workshop|facilita|structure|phase)/);
    expect(content).toMatch(/(solution|creative|innovative)/);

    // Performance validation
    expect(responseTime).toBeLessThan(100000);
    expect(response.length).toBeGreaterThan(500);

    console.log(`✅ Design thinking workshop completed in ${responseTime}ms`);
    console.log(`💡 Creative problem-solving methodology provided`);
  });

  test.afterEach(async ({ page }) => {
    if (test.info().status === "failed") {
      await debugScreenshot(page, `creative-workflows-${test.info().title}`);
    }
  });
});
