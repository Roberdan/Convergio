/**
 * Validation Helpers for Convergio E2E Tests
 * Utilities for validating AI responses and system behavior
 */

import { expect } from "@playwright/test";
import type { AgentResponse } from "./agent-helpers";

export interface ValidationCriteria {
  minLength?: number;
  maxLength?: number;
  mustContain?: string[];
  mustNotContain?: string[];
  mustHaveStructure?: boolean;
  mustHaveNumbers?: boolean;
  mustHaveDates?: boolean;
  mustHaveUrls?: boolean;
}

/**
 * Comprehensive AI response validation
 */
export function validateAIResponse(
  response: AgentResponse,
  criteria: ValidationCriteria = {},
): boolean {
  const { message } = response;
  const {
    minLength = 100,
    maxLength = 10000,
    mustContain = [],
    mustNotContain = [],
    mustHaveStructure = false,
    mustHaveNumbers = false,
    mustHaveDates = false,
    mustHaveUrls = false,
  } = criteria;

  // Basic length validation
  if (message.length < minLength || message.length > maxLength) {
    console.log(
      `Response length ${message.length} outside range ${minLength}-${maxLength}`,
    );
    return false;
  }

  // Content requirements
  for (const required of mustContain) {
    if (!message.toLowerCase().includes(required.toLowerCase())) {
      console.log(`Response missing required content: ${required}`);
      return false;
    }
  }

  // Content prohibitions
  for (const forbidden of mustNotContain) {
    if (message.toLowerCase().includes(forbidden.toLowerCase())) {
      console.log(`Response contains forbidden content: ${forbidden}`);
      return false;
    }
  }

  // Structure validation
  if (mustHaveStructure) {
    const hasStructure =
      message.includes("\n") ||
      message.includes("•") ||
      message.includes("-") ||
      /\d+\./.test(message) ||
      message.includes("**") ||
      message.includes("##");
    if (!hasStructure) {
      console.log("Response lacks required structure");
      return false;
    }
  }

  // Numbers validation
  if (mustHaveNumbers) {
    const hasNumbers = /\d/.test(message);
    if (!hasNumbers) {
      console.log("Response lacks required numbers");
      return false;
    }
  }

  // Date validation
  if (mustHaveDates) {
    const datePatterns = [
      /\d{4}/, // Year
      /\d{1,2}\/\d{1,2}/, // Date
      /(january|february|march|april|may|june|july|august|september|october|november|december)/i,
      /(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i,
    ];
    const hasDates = datePatterns.some((pattern) => pattern.test(message));
    if (!hasDates) {
      console.log("Response lacks required dates");
      return false;
    }
  }

  // URL validation
  if (mustHaveUrls) {
    const hasUrls = /https?:\/\//.test(message);
    if (!hasUrls) {
      console.log("Response lacks required URLs");
      return false;
    }
  }

  return true;
}

/**
 * Validate Ali Chief of Staff response quality
 */
export function validateAliResponse(response: AgentResponse): boolean {
  return validateAIResponse(response, {
    minLength: 150,
    mustHaveStructure: true,
    mustNotContain: ["error", "cannot", "unable", "fallback"],
  });
}

/**
 * Validate Amy CFO financial analysis response
 */
export function validateAmyFinancialResponse(response: AgentResponse): boolean {
  return validateAIResponse(response, {
    minLength: 200,
    mustHaveNumbers: true,
    mustHaveStructure: true,
    mustContain: ["budget", "cost", "revenue", "ROI"],
  });
}

/**
 * Validate Marcus PM project response
 */
export function validateMarcusProjectResponse(
  response: AgentResponse,
): boolean {
  return validateAIResponse(response, {
    minLength: 150,
    mustHaveStructure: true,
    mustContain: ["timeline", "milestone", "deliverable"],
    mustHaveDates: true,
  });
}

/**
 * Validate internet research response (with Perplexity)
 */
export function validateResearchResponse(response: AgentResponse): boolean {
  return validateAIResponse(response, {
    minLength: 200,
    mustHaveStructure: true,
    mustHaveUrls: true,
    mustNotContain: ["I cannot access", "no internet", "unable to search"],
  });
}

/**
 * Validate multi-agent orchestration results
 */
export function validateOrchestration(responses: AgentResponse[]): boolean {
  if (responses.length < 2) {
    console.log("Orchestration must involve at least 2 agents");
    return false;
  }

  // Each response should be high quality
  for (const response of responses) {
    if (!validateAIResponse(response, { minLength: 50 })) {
      console.log(`Poor quality response from ${response.agent}`);
      return false;
    }
  }

  // Responses should be related/coherent
  const allContent = responses
    .map((r) => r.message)
    .join(" ")
    .toLowerCase();
  const hasCoherence =
    responses.length < 3 ||
    responses.some(
      (r, i) =>
        i > 0 &&
        responses
          .slice(0, i)
          .some(
            (prev) =>
              r.message.toLowerCase().includes(prev.agent.toLowerCase()) ||
              prev.message.toLowerCase().includes(r.agent.toLowerCase()),
          ),
    );

  if (!hasCoherence) {
    console.log("Orchestration responses lack coherence");
    return false;
  }

  return true;
}

/**
 * Business-specific validation for Convergio use cases
 */
export interface BusinessValidation {
  hasStrategicThinking?: boolean;
  hasActionableInsights?: boolean;
  hasDataDriven?: boolean;
  hasRisksConsideration?: boolean;
  hasTimeframes?: boolean;
  hasMetrics?: boolean;
}

export function validateBusinessResponse(
  response: AgentResponse,
  criteria: BusinessValidation = {},
): boolean {
  const { message } = response;
  const {
    hasStrategicThinking = false,
    hasActionableInsights = false,
    hasDataDriven = false,
    hasRisksConsideration = false,
    hasTimeframes = false,
    hasMetrics = false,
  } = criteria;

  if (hasStrategicThinking) {
    const strategicTerms = [
      "strategy",
      "strategic",
      "opportunity",
      "competitive",
      "market",
      "growth",
    ];
    const hasStrategy = strategicTerms.some((term) =>
      message.toLowerCase().includes(term),
    );
    if (!hasStrategy) return false;
  }

  if (hasActionableInsights) {
    const actionTerms = [
      "recommend",
      "suggest",
      "should",
      "action",
      "implement",
      "execute",
    ];
    const hasActions = actionTerms.some((term) =>
      message.toLowerCase().includes(term),
    );
    if (!hasActions) return false;
  }

  if (hasDataDriven) {
    const dataTerms = [
      "data",
      "metric",
      "measurement",
      "analysis",
      "insight",
      "trend",
    ];
    const hasData = dataTerms.some((term) =>
      message.toLowerCase().includes(term),
    );
    if (!hasData) return false;
  }

  if (hasRisksConsideration) {
    const riskTerms = [
      "risk",
      "challenge",
      "concern",
      "mitigation",
      "threat",
      "obstacle",
    ];
    const hasRisks = riskTerms.some((term) =>
      message.toLowerCase().includes(term),
    );
    if (!hasRisks) return false;
  }

  if (hasTimeframes) {
    const timePatterns = [
      /\d+\s+(days?|weeks?|months?|quarters?|years?)/i,
      /(q[1-4]|quarter)/i,
      /(short|medium|long).term/i,
      /\d{4}/,
    ];
    const hasTime = timePatterns.some((pattern) => pattern.test(message));
    if (!hasTime) return false;
  }

  if (hasMetrics) {
    const metricPatterns = [
      /\d+%/,
      /\$[\d,]+/,
      /\d+[km]?\s*(users?|customers?|revenue)/i,
      /(roi|roas|ltv|cac|mrr|arr)/i,
    ];
    const hasMetrics = metricPatterns.some((pattern) => pattern.test(message));
    if (!hasMetrics) return false;
  }

  return true;
}

/**
 * Performance validation helper
 */
export interface PerformanceMetrics {
  responseTime: number;
  contentLength: number;
  errorCount: number;
}

export function validatePerformance(
  metrics: PerformanceMetrics,
  maxResponseTime: number = 30000,
  minContentLength: number = 100,
): boolean {
  if (metrics.responseTime > maxResponseTime) {
    console.log(
      `Response time ${metrics.responseTime}ms exceeds ${maxResponseTime}ms`,
    );
    return false;
  }

  if (metrics.contentLength < minContentLength) {
    console.log(
      `Content length ${metrics.contentLength} below minimum ${minContentLength}`,
    );
    return false;
  }

  if (metrics.errorCount > 0) {
    console.log(`Found ${metrics.errorCount} errors during execution`);
    return false;
  }

  return true;
}

/**
 * Playwright assertion helpers for better test readability
 */
export async function expectAIResponse(
  response: AgentResponse,
  criteria: ValidationCriteria = {},
) {
  expect(
    validateAIResponse(response, criteria),
    `AI response validation failed for ${response.agent}: ${response.message.substring(0, 100)}...`,
  ).toBe(true);
}

export async function expectBusinessResponse(
  response: AgentResponse,
  criteria: BusinessValidation = {},
) {
  expect(
    validateBusinessResponse(response, criteria),
    `Business validation failed for ${response.agent}: ${response.message.substring(0, 100)}...`,
  ).toBe(true);
}

export async function expectOrchestration(responses: AgentResponse[]) {
  expect(
    validateOrchestration(responses),
    `Orchestration validation failed for ${responses.length} agent responses`,
  ).toBe(true);
}
