/**
 * Industry Specialization E2E Tests
 * Tests specialized agent expertise for real-world industry use cases
 * Validates the 48-agent ecosystem's ability to handle domain-specific scenarios
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

test.describe("Industry Specialization - Real-World Use Cases", () => {
  test.beforeEach(async ({ page }) => {
    await loginTestUser(page);
    await clearConversation(page);
  });

  test("Healthcare & Compliance - HIPAA and Medical Device Regulation", async ({
    page,
  }) => {
    // Test healthcare expertise with Dr. Enzo
    await navigateToAgent(page, "dr_enzo_healthcare_compliance_manager");

    const healthcareQuery = `Dr. Enzo, stiamo sviluppando una piattaforma di telemedicine per cardiologia. 
    
    Requisiti di compliance:
    - HIPAA compliance per dati pazienti negli USA
    - GDPR per pazienti europei
    - FDA clearance per medical device software (Class II)
    - Integration con sistemi ospedalieri (HL7 FHIR)
    - Real-time monitoring di device medicali (ECG, blood pressure)
    
    Fornisci una compliance strategy completa e roadmap per regulatory approval.`;

    const startTime = Date.now();

    await sendAgentQuery(
      page,
      "dr_enzo_healthcare_compliance_manager",
      healthcareQuery,
    );

    const response = await getLatestAgentResponse(page, 90000);
    const responseTime = Date.now() - startTime;

    // Validate healthcare compliance expertise
    await expectAIResponse(response, {
      minLength: 400,
      mustHaveStructure: true,
      mustContain: ["hipaa", "gdpr", "fda", "compliance"],
    });

    // Healthcare-specific validation
    const content = response.message.toLowerCase();

    // Should include regulatory knowledge
    expect(content).toMatch(/(hipaa|health.insurance.portability)/);
    expect(content).toMatch(/(fda|food.drug.administration|medical.device)/);
    expect(content).toMatch(/(gdpr|data.protection|privacy)/);
    expect(content).toMatch(/(hl7|fhir|interoperability)/);

    // Should include medical device expertise
    expect(content).toMatch(/(class.ii|medical.device|510k|clearance)/);
    expect(content).toMatch(/(telemedicine|cardiology|ecg|blood.pressure)/);
    expect(content).toMatch(/(patient.data|phi|protected.health)/);

    // Should provide regulatory guidance
    expect(content).toMatch(
      /(compliance.strategy|regulatory|approval|roadmap)/,
    );
    expect(content).toMatch(/(audit|documentation|validation|certification)/);

    // Performance validation
    expect(responseTime).toBeLessThan(120000);
    expect(response.length).toBeGreaterThan(500);

    console.log(
      `✅ Healthcare compliance expertise validated in ${responseTime}ms`,
    );
    console.log(`🏥 HIPAA, FDA, and GDPR regulatory guidance provided`);
  });

  test("Financial Services - FinTech Regulatory and Security Architecture", async ({
    page,
  }) => {
    // Test financial services expertise with coordinated team
    await navigateToAgent(page, "ali_chief_of_staff");

    const fintechQuery = `Ali, coordina Luca (Security), Elena (Legal Compliance), Amy (CFO), e Baccio (Tech) 
    per lanciare una piattaforma di digital banking in Europa.
    
    SFIDE:
    - PCI DSS Level 1 compliance per pagamenti
    - PSD2 compliance per open banking APIs
    - GDPR per dati finanziari sensibili
    - Anti-money laundering (AML) e Know Your Customer (KYC)
    - Real-time fraud detection con ML
    - Multi-country regulatory frameworks (Germania, Francia, Italia)
    - High-frequency transaction processing (1M+ daily)
    
    Voglio una soluzione completa per entrare nel mercato fintech europeo.`;

    const startTime = Date.now();

    await sendAliQuery(page, fintechQuery);

    const responses = await waitForOrchestration(page, ["ali"], 180000);
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const fintechResponse = responses[0];
    const content = fintechResponse.message.toLowerCase();

    // Should demonstrate FinTech expertise
    expect(content).toMatch(/(fintech|financial.services|digital.banking)/);
    expect(content).toMatch(/(pci.dss|psd2|gdpr|aml|kyc)/);
    expect(content).toMatch(/(fraud.detection|ml|machine.learning)/);

    // Should include specialized financial regulations
    const hasPaymentCompliance = /pci.dss|payment.card|level.1|compliance/.test(
      content,
    );
    const hasOpenBanking = /psd2|open.banking|api|payment.service/.test(
      content,
    );
    const hasAMLKYC = /aml|anti.money.laundering|kyc|know.your.customer/.test(
      content,
    );
    const hasFraudPrevention = /fraud|detection|ml|security|transaction/.test(
      content,
    );
    const hasMultiCountry =
      /multi.country|germania|francia|italia|european/.test(content);

    const fintechAreas = [
      hasPaymentCompliance,
      hasOpenBanking,
      hasAMLKYC,
      hasFraudPrevention,
      hasMultiCountry,
    ].filter(Boolean).length;
    expect(fintechAreas).toBeGreaterThanOrEqual(4);

    // Should address high-frequency processing
    expect(content).toMatch(
      /(1m|million|high.frequency|transaction.processing)/,
    );
    expect(content).toMatch(/(scalab|performance|real.time)/);

    // Business validation for FinTech
    await expectBusinessResponse(fintechResponse, {
      hasStrategicThinking: true,
      hasRisksConsideration: true,
      hasActionableInsights: true,
    });

    expect(totalTime).toBeLessThan(240000);
    expect(fintechResponse.length).toBeGreaterThan(600);

    console.log(
      `✅ FinTech regulatory coordination completed in ${totalTime}ms`,
    );
    console.log(
      `💳 FinTech areas: PCI=${hasPaymentCompliance}, PSD2=${hasOpenBanking}, AML/KYC=${hasAMLKYC}, Fraud=${hasFraudPrevention}, MultiCountry=${hasMultiCountry}`,
    );
  });

  test("Manufacturing & Supply Chain - Industry 4.0 Digital Transformation", async ({
    page,
  }) => {
    // Test manufacturing and supply chain expertise
    await navigateToAgent(page, "ali_chief_of_staff");

    const manufacturingQuery = `Ali, coordina il team per trasformare una manufacturing company tradizionale 
    in Industry 4.0 smart factory.
    
    CONTESTO:
    - 5 stabilimenti produttivi in Europa (automotive parts)
    - 2,000 dipendenti, macchine legacy da modernizzare
    - Supply chain complessa con 200+ fornitori
    - Quality control manuale da automatizzare
    - Sustainability targets: -30% CO2 entro 2026
    
    OBIETTIVI INDUSTRY 4.0:
    - IoT sensors per predictive maintenance
    - Digital twin per simulation e optimization
    - AI-powered quality control con computer vision
    - Supply chain visibility e risk management
    - Energy management e carbon footprint tracking
    - Worker safety e augmented reality per training
    
    Coordinate tutti gli expert: Tech Architecture, Data Science, Operations, Sustainability.`;

    const startTime = Date.now();

    await sendAliQuery(page, manufacturingQuery);

    const responses = await waitForOrchestration(page, ["ali"], 180000);
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const industryResponse = responses[0];
    const content = industryResponse.message.toLowerCase();

    // Should demonstrate Industry 4.0 expertise
    expect(content).toMatch(
      /(industry.4\.0|smart.factory|manufacturing|digital.transformation)/,
    );
    expect(content).toMatch(
      /(iot|sensors|predictive.maintenance|digital.twin)/,
    );
    expect(content).toMatch(
      /(automotive|supply.chain|fornitori|sustainability)/,
    );

    // Should include Industry 4.0 technologies
    const hasIoTPredictive =
      /iot|sensors|predictive.maintenance|machine.learning/.test(content);
    const hasDigitalTwin = /digital.twin|simulation|optimization|virtual/.test(
      content,
    );
    const hasAIQuality = /ai|computer.vision|quality.control|automated/.test(
      content,
    );
    const hasSupplyChain =
      /supply.chain|visibility|risk.management|200.fornitori/.test(content);
    const hasSustainability = /sustainability|co2|carbon|energy|30%/.test(
      content,
    );
    const hasAR = /augmented.reality|ar|training|worker.safety/.test(content);

    const industry40Features = [
      hasIoTPredictive,
      hasDigitalTwin,
      hasAIQuality,
      hasSupplyChain,
      hasSustainability,
      hasAR,
    ].filter(Boolean).length;
    expect(industry40Features).toBeGreaterThanOrEqual(4);

    // Should address scale and complexity
    expect(content).toMatch(/(5.stabilimenti|2000.dipendenti|200.fornitori)/);
    expect(content).toMatch(/(europa|automotive|legacy.moderniz)/);

    await expectBusinessResponse(industryResponse, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
      hasTimeframes: true,
    });

    expect(totalTime).toBeLessThan(240000);
    expect(industryResponse.length).toBeGreaterThan(700);

    console.log(
      `✅ Industry 4.0 manufacturing transformation completed in ${totalTime}ms`,
    );
    console.log(
      `🏭 Industry 4.0 features: IoT=${hasIoTPredictive}, DigitalTwin=${hasDigitalTwin}, AI=${hasAIQuality}, Supply=${hasSupplyChain}, Sustainability=${hasSustainability}, AR=${hasAR}`,
    );
  });

  test("Government & Public Sector - Smart City Infrastructure", async ({
    page,
  }) => {
    // Test government affairs expertise with Sophia
    await navigateToAgent(page, "sophia_government_affairs");

    const smartCityQuery = `Sophia, stiamo sviluppando una piattaforma Smart City per il Comune di Milano. 
    
    PROGETTO SMART CITY:
    - Traffic management con IoT e AI (semafori intelligenti)
    - Energy grid optimization per sustainability
    - Citizen services digitalization (permessi, anagrafe online)
    - Public safety: video surveillance con facial recognition
    - Waste management optimization con sensori
    - Air quality monitoring e reporting
    
    SFIDE GOVERNANCE:
    - Privacy citizens (GDPR + normativa italiana)
    - Public procurement regulations (Codice Appalti)
    - Interoperability con sistemi regionali Lombardia
    - Digital divide e accessibility per anziani
    - Cybersecurity per infrastrutture critiche
    - Budget pubblico e EU funding opportunities
    
    Fornisci strategic guidance per navigare regulatory framework e implementazione.`;

    const startTime = Date.now();

    await sendAgentQuery(page, "sophia_government_affairs", smartCityQuery);

    const response = await getLatestAgentResponse(page, 120000);
    const responseTime = Date.now() - startTime;

    // Validate government affairs expertise
    await expectAIResponse(response, {
      minLength: 450,
      mustHaveStructure: true,
      mustContain: ["smart city", "government", "regulatory"],
    });

    // Government-specific validation
    const content = response.message.toLowerCase();

    // Should include public sector expertise
    expect(content).toMatch(/(smart.city|government|public.sector|comune)/);
    expect(content).toMatch(/(gdpr|privacy|citizen|procurement)/);
    expect(content).toMatch(/(milan|lombardia|italian|normativa)/);

    // Should include smart city technologies
    const hasTrafficManagement = /traffic|semafori|iot|ai|intelligent/.test(
      content,
    );
    const hasEnergyGrid = /energy|grid|optimization|sustainability/.test(
      content,
    );
    const hasCitizenServices =
      /citizen.services|digital|permessi|anagrafe/.test(content);
    const hasPublicSafety =
      /public.safety|surveillance|facial.recognition/.test(content);
    const hasWasteManagement = /waste.management|sensor|optimization/.test(
      content,
    );

    // Should address regulatory challenges
    const hasPrivacyGDPR = /privacy|gdpr|citizen|data.protection/.test(content);
    const hasProcurement = /procurement|codice.appalti|public|tender/.test(
      content,
    );
    const hasInteroperability =
      /interoperability|regiona|lombardia|integration/.test(content);
    const hasAccessibility =
      /accessibility|digital.divide|anziani|inclusion/.test(content);
    const hasCybersecurity =
      /cybersecurity|security|infrastructure|critical/.test(content);

    const smartCityAreas = [
      hasTrafficManagement,
      hasEnergyGrid,
      hasCitizenServices,
      hasPublicSafety,
      hasWasteManagement,
    ].filter(Boolean).length;
    const regulatoryAreas = [
      hasPrivacyGDPR,
      hasProcurement,
      hasInteroperability,
      hasAccessibility,
      hasCybersecurity,
    ].filter(Boolean).length;

    expect(smartCityAreas).toBeGreaterThanOrEqual(3);
    expect(regulatoryAreas).toBeGreaterThanOrEqual(3);

    // Should include EU funding guidance
    expect(content).toMatch(/(eu.funding|european|grant|finanziament)/);

    expect(responseTime).toBeLessThan(150000);
    expect(response.length).toBeGreaterThan(550);

    console.log(
      `✅ Smart city government affairs completed in ${responseTime}ms`,
    );
    console.log(
      `🏛️ Smart city areas covered: ${smartCityAreas}, Regulatory areas: ${regulatoryAreas}`,
    );
  });

  test("Education Technology - AI-Powered Learning Platform", async ({
    page,
  }) => {
    // Test EdTech with accessibility and inclusive design
    await navigateToAgent(page, "ali_chief_of_staff");

    const edtechQuery = `Ali, coordina Jenny (Accessibility), Sara (UX), Omri (Data Scientist), e Coach 
    per creare una piattaforma AI-powered per l'educazione inclusiva.
    
    VISION EDTECH:
    - Personalized learning paths con ML algorithms
    - Accessibility-first design (WCAG AAA compliance)
    - Multi-language support e cultural adaptation
    - Real-time learning analytics per teachers
    - Gamification e engagement per studenti
    - Integration con LMS esistenti (Moodle, Canvas)
    
    OBIETTIVI INCLUSIVI:
    - Support per learning disabilities (dyslexia, ADHD)
    - Screen reader compatibility totale
    - Motor impairment accommodation
    - Economic accessibility (low-bandwidth optimization)
    - Cultural sensitivity per diverse communities
    - Teacher training e support programs
    
    Focus: democratizzare l'accesso all'educazione di qualità attraverso AI inclusiva.`;

    const startTime = Date.now();

    await sendAliQuery(page, edtechQuery);

    const responses = await waitForOrchestration(page, ["ali"], 150000);
    const totalTime = Date.now() - startTime;

    expect(responses.length).toBeGreaterThanOrEqual(1);

    const edtechResponse = responses[0];
    const content = edtechResponse.message.toLowerCase();

    // Should demonstrate EdTech expertise
    expect(content).toMatch(/(edtech|education|learning|ai.powered)/);
    expect(content).toMatch(/(accessibility|inclusive|wcag|disability)/);
    expect(content).toMatch(/(personalized|ml|algorithm|analytics)/);

    // Should include EdTech features
    const hasPersonalizedLearning =
      /personalized|learning.path|ml|algorithm|adaptive/.test(content);
    const hasAccessibilityFirst =
      /accessibility|wcag|aaa|screen.reader|inclusive/.test(content);
    const hasMultiLanguage =
      /multi.language|cultural|adaptation|diversity/.test(content);
    const hasLearningAnalytics =
      /analytics|teacher|real.time|data|insight/.test(content);
    const hasGamification = /gamification|engagement|student|motivation/.test(
      content,
    );

    // Should address inclusion challenges
    const hasLearningDisabilities =
      /learning.disabilit|dyslexia|adhd|special.need/.test(content);
    const hasMotorAccommodation =
      /motor|impairment|accommodation|physical/.test(content);
    const hasEconomicAccess =
      /economic|low.bandwidth|optimization|affordable/.test(content);
    const hasCulturalSensitivity =
      /cultural|sensitivity|diverse.communities|inclusion/.test(content);

    const edtechFeatures = [
      hasPersonalizedLearning,
      hasAccessibilityFirst,
      hasMultiLanguage,
      hasLearningAnalytics,
      hasGamification,
    ].filter(Boolean).length;
    const inclusionFeatures = [
      hasLearningDisabilities,
      hasMotorAccommodation,
      hasEconomicAccess,
      hasCulturalSensitivity,
    ].filter(Boolean).length;

    expect(edtechFeatures).toBeGreaterThanOrEqual(4);
    expect(inclusionFeatures).toBeGreaterThanOrEqual(3);

    // Should focus on democratization
    expect(content).toMatch(
      /(democratiz|access|quality.education|inclusive.ai)/,
    );

    await expectBusinessResponse(edtechResponse, {
      hasStrategicThinking: true,
      hasActionableInsights: true,
    });

    expect(totalTime).toBeLessThan(200000);
    expect(edtechResponse.length).toBeGreaterThan(600);

    console.log(
      `✅ EdTech inclusive platform design completed in ${totalTime}ms`,
    );
    console.log(
      `📚 EdTech features: ${edtechFeatures}, Inclusion features: ${inclusionFeatures}`,
    );
    console.log(`♿ Accessibility-first AI education platform designed`);
  });

  test("Venture Capital & Investment - Startup Portfolio Analysis", async ({
    page,
  }) => {
    // Test VC expertise with Michael and Wiz
    await navigateToAgent(page, "michael_venture_capitalist");

    const vcQuery = `Michael, analizza questo portfolio di startup per il nostro VC fund:
    
    PORTFOLIO ANALYSIS REQUEST:
    1. FinTech Startup "PayFlow" - Series A, $5M raised, 200% YoY growth
       - B2B payment processing per SMEs
       - Monthly revenue: $150K, burn rate: $80K
       - Competition: Stripe, Square, strong moat con ML fraud detection
    
    2. HealthTech "MedAI" - Seed stage, $2M raised, early traction
       - AI diagnostics per radiology (FDA approval pending)
       - Pilot con 5 ospedali, 94% accuracy vs human radiologists
       - Market: $12B radiology, team Harvard Medical School
    
    3. CleanTech "SolarGrid" - Series B, $15M raised, scaling issues
       - Smart solar energy management per residential
       - Revenue: $300K/month, but margins dropping (25% → 18%)
       - Competition intensifying, customer acquisition costs rising
    
    Provide: investment thesis, risk assessment, portfolio recommendations, exit strategies.`;

    const startTime = Date.now();

    await sendAgentQuery(page, "michael_venture_capitalist", vcQuery);

    const response = await getLatestAgentResponse(page, 120000);
    const responseTime = Date.now() - startTime;

    // Validate VC expertise
    await expectAIResponse(response, {
      minLength: 500,
      mustHaveStructure: true,
      mustContain: ["investment", "portfolio", "startup", "analysis"],
    });

    // VC-specific validation
    const content = response.message.toLowerCase();

    // Should include VC terminology and analysis
    expect(content).toMatch(
      /(investment.thesis|portfolio|due.diligence|exit.strategy)/,
    );
    expect(content).toMatch(/(series.a|series.b|seed|valuation|burn.rate)/);
    expect(content).toMatch(/(payflow|medai|solargrid)/); // Portfolio companies

    // Should analyze each startup sector
    const hasFinTechAnalysis =
      /payflow|fintech|payment|stripe|square|fraud.detection/.test(content);
    const hasHealthTechAnalysis =
      /medai|healthtech|ai.diagnostics|fda|radiology/.test(content);
    const hasCleanTechAnalysis =
      /solargrid|cleantech|solar|energy|margins|acquisition/.test(content);

    expect(hasFinTechAnalysis).toBe(true);
    expect(hasHealthTechAnalysis).toBe(true);
    expect(hasCleanTechAnalysis).toBe(true);

    // Should include investment analysis elements
    const hasRiskAssessment =
      /risk|assessment|challenge|concern|mitigation/.test(content);
    const hasGrowthMetrics = /growth|revenue|yoy|200%|traction|scale/.test(
      content,
    );
    const hasCompetitiveAnalysis =
      /competition|competitive|moat|advantage|differentiat/.test(content);
    const hasExitStrategy = /exit|strategy|acquisition|ipo|liquidity/.test(
      content,
    );

    const vcAnalysisAreas = [
      hasRiskAssessment,
      hasGrowthMetrics,
      hasCompetitiveAnalysis,
      hasExitStrategy,
    ].filter(Boolean).length;
    expect(vcAnalysisAreas).toBeGreaterThanOrEqual(3);

    // Should provide actionable recommendations
    expect(content).toMatch(/(recommend|suggest|advise|strategy|next.step)/);
    expect(content).toMatch(/(valuation|investment|follow.on|portfolio)/);

    expect(responseTime).toBeLessThan(150000);
    expect(response.length).toBeGreaterThan(600);

    console.log(`✅ VC portfolio analysis completed in ${responseTime}ms`);
    console.log(
      `💰 Sectors analyzed: FinTech=${hasFinTechAnalysis}, HealthTech=${hasHealthTechAnalysis}, CleanTech=${hasCleanTechAnalysis}`,
    );
    console.log(`📈 Investment analysis areas covered: ${vcAnalysisAreas}`);
  });

  test.afterEach(async ({ page }) => {
    if (test.info().status === "failed") {
      await debugScreenshot(
        page,
        `industry-specialization-${test.info().title}`,
      );
    }
  });
});
