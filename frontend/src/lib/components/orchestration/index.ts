// CRM-Style PM Orchestration Components
// AI-orchestrated project management with real-time monitoring

export { default as PMOrchestrationDashboard } from "./PMOrchestrationDashboard.svelte";
export { default as ProjectJourneyVisualization } from "./ProjectJourneyVisualization.svelte";
export { default as AgentCollaborationPanel } from "./AgentCollaborationPanel.svelte";
export { default as OrchestrationMetricsCard } from "./OrchestrationMetricsCard.svelte";
export { default as RealTimeStreamingMonitor } from "./RealTimeStreamingMonitor.svelte";
export { default as TouchpointTimeline } from "./TouchpointTimeline.svelte";

// Component Types and Interfaces
export interface OrchestrationData {
  id: string;
  orchestration_status: string;
  current_stage: string;
  primary_agent: string;
  ai_efficiency_score: number;
  agent_collaboration_score: number;
  satisfaction_score: number;
  touchpoint_count: number;
  agent_assignments: AgentAssignment[];
  journey_stages: JourneyStage[];
  recent_touchpoints: Touchpoint[];
  real_time_metrics: any;
}

export interface AgentAssignment {
  agent_name: string;
  agent_role: string;
  efficiency_score: number;
  collaboration_score: number;
  tasks_completed: number;
  cost_incurred: number;
  active: boolean;
}

export interface JourneyStage {
  stage_name: string;
  status: string;
  progress_percentage: number;
  satisfaction_score: number;
  start_date: string;
  primary_agents: string[];
}

export interface Touchpoint {
  id: string;
  touchpoint_type: string;
  title: string;
  initiated_by: string;
  interaction_date: string;
  satisfaction_score: number;
  participants: string[];
}

export interface StreamingUpdate {
  id: string;
  type: string;
  timestamp: string;
  data: any;
  agent?: string;
  priority: "low" | "medium" | "high";
}
