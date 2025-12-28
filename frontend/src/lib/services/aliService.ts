/**
 * 🤖 Ali Chief of Staff Service
 * Central service for all Ali interactions with the backend
 */

import { writable } from "svelte/store";

export interface AliResponse {
  response: string;
  agents_used?: string[];
  iterations?: any[];
  confidence?: number;
  suggestions?: any[];
}

export interface AliAnalysis {
  suggestions: any[];
  confidence: number;
  categories: {
    expertise: any[];
    tools: any[];
    persona: any[];
    coordination: any[];
  };
}

class AliService {
  private baseUrl = `${import.meta.env.VITE_API_URL || "http://localhost:9000"}/api/v1`;
  private wsUrl = `${import.meta.env.VITE_API_URL?.replace("http", "ws") || "ws://localhost:9000"}/api/v1`;

  // Store for Ali's connection status
  public connectionStatus = writable<
    "connected" | "connecting" | "disconnected" | "error"
  >("disconnected");
  public latency = writable<number>(0);

  /**
   * Send a message to Ali via the conversation API
   */
  async sendMessage(message: string, context?: any): Promise<AliResponse> {
    try {
      const startTime = Date.now();

      const response = await fetch(`${this.baseUrl}/agents/ali/intelligence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          context: {
            source: "ali_service",
            role: "ceo",
            interface: "agent_interface",
            ...context,
          },
          use_vector_search: true,
          use_database_insights: true,
          include_strategic_analysis: true,
        }),
      });

      const latency = Date.now() - startTime;
      this.latency.set(latency);

      if (!response.ok) {
        throw new Error(`Ali responded with status ${response.status}`);
      }

      const result = await response.json();
      this.connectionStatus.set("connected");

      return result;
    } catch (error) {
      // Silent failure
      this.connectionStatus.set("error");
      throw error;
    }
  }

  /**
   * Analyze an agent definition using Ali's expertise
   */
  async analyzeAgentDefinition(definition: any): Promise<AliAnalysis> {
    try {
      const response = await this.sendMessage(
        `Analyze this agent definition and provide specific improvement suggestions: ${JSON.stringify(definition)}`,
        {
          mode: "analysis",
          definition,
        },
      );

      return this.parseAnalysisResponse(response);
    } catch (error) {
      // Silent failure
      return {
        suggestions: [],
        confidence: 0,
        categories: {
          expertise: [],
          tools: [],
          persona: [],
          coordination: [],
        },
      };
    }
  }

  /**
   * Start oversight mode with WebSocket for real-time updates
   */
  startOversightMode(conversationId: string): WebSocket {
    const ws = new WebSocket(
      `${this.wsUrl}/agents/ws/conversation/${conversationId}`,
    );

    ws.onopen = () => {
      this.connectionStatus.set("connected");
    };

    ws.onerror = (error) => {
      // Silent failure
      this.connectionStatus.set("error");
    };

    ws.onclose = () => {
      this.connectionStatus.set("disconnected");
    };

    return ws;
  }

  /**
   * Get Ali's status and ecosystem information
   */
  async getEcosystemStatus(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/ecosystem`);

      if (!response.ok) {
        throw new Error("Failed to get ecosystem status");
      }

      const status = await response.json();
      this.connectionStatus.set("connected");

      return status;
    } catch (error) {
      // Silent failure
      this.connectionStatus.set("error");
      return null;
    }
  }

  /**
   * Request an executive brief from Ali
   */
  async requestExecutiveBrief(): Promise<string> {
    try {
      const response = await this.sendMessage(
        "Provide executive summary of all current projects, key metrics, and strategic recommendations",
        {
          role: "ceo",
          source: "dashboard",
        },
      );

      return response.response;
    } catch (error) {
      // Silent failure
      return "Unable to generate executive brief at this time.";
    }
  }

  /**
   * Parse Ali's response into structured analysis
   */
  private parseAnalysisResponse(response: AliResponse): AliAnalysis {
    const analysis: AliAnalysis = {
      suggestions: [],
      confidence: 0.85,
      categories: {
        expertise: [],
        tools: [],
        persona: [],
        coordination: [],
      },
    };

    const responseText = response.response || "";

    // Extract suggestions based on keywords in Ali's response
    if (
      responseText.toLowerCase().includes("expertise") ||
      responseText.toLowerCase().includes("skill")
    ) {
      analysis.suggestions.push({
        id: `suggestion-${Date.now()}`,
        category: "expertise",
        type: "enhancement",
        priority: "high",
        title: "Expertise Enhancement",
        description: "Ali recommends expanding expertise areas",
        suggestion: this.extractSuggestion(responseText, "expertise"),
        impact: "Improved specialization and task routing",
        effort: "low",
        autoApplicable: true,
      });
    }

    if (
      responseText.toLowerCase().includes("tool") ||
      responseText.toLowerCase().includes("capability")
    ) {
      analysis.suggestions.push({
        id: `suggestion-${Date.now()}`,
        category: "tools",
        type: "addition",
        priority: "medium",
        title: "Tool Enhancement",
        description: "Ali suggests adding new tools",
        suggestion: this.extractSuggestion(responseText, "tools"),
        impact: "Enhanced capabilities",
        effort: "low",
        autoApplicable: true,
      });
    }

    if (
      responseText.toLowerCase().includes("persona") ||
      responseText.toLowerCase().includes("personality")
    ) {
      analysis.suggestions.push({
        id: `suggestion-${Date.now()}`,
        category: "persona",
        type: "enhancement",
        priority: "medium",
        title: "Persona Development",
        description: "Ali recommends enriching agent persona",
        suggestion: this.extractSuggestion(responseText, "persona"),
        impact: "Better user interactions",
        effort: "medium",
        autoApplicable: false,
      });
    }

    if (
      responseText.toLowerCase().includes("coordination") ||
      responseText.toLowerCase().includes("collaborate")
    ) {
      analysis.suggestions.push({
        id: `suggestion-${Date.now()}`,
        category: "coordination",
        type: "enhancement",
        priority: "high",
        title: "Coordination Improvement",
        description: "Ali suggests better agent coordination",
        suggestion: this.extractSuggestion(responseText, "coordination"),
        impact: "Improved team efficiency",
        effort: "medium",
        autoApplicable: true,
      });
    }

    // Categorize suggestions
    analysis.categories.expertise = analysis.suggestions.filter(
      (s) => s.category === "expertise",
    );
    analysis.categories.tools = analysis.suggestions.filter(
      (s) => s.category === "tools",
    );
    analysis.categories.persona = analysis.suggestions.filter(
      (s) => s.category === "persona",
    );
    analysis.categories.coordination = analysis.suggestions.filter(
      (s) => s.category === "coordination",
    );

    // Set confidence based on response quality
    if (response.agents_used && response.agents_used.length > 0) {
      analysis.confidence = Math.min(
        0.95,
        0.7 + response.agents_used.length * 0.05,
      );
    }

    return analysis;
  }

  /**
   * Extract specific suggestion from Ali's response
   */
  private extractSuggestion(text: string, category: string): string {
    const sentences = text.split(/[.!?]+/);
    const relevant = sentences.find(
      (s) =>
        s.toLowerCase().includes(category) ||
        s.toLowerCase().includes("suggest") ||
        s.toLowerCase().includes("recommend"),
    );

    return relevant?.trim() || `Consider improvements in ${category}`;
  }
}

// Export singleton instance
export const aliService = new AliService();
