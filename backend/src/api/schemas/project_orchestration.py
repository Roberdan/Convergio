"""
Pydantic Schemas for Enhanced PM Orchestration API
Request/Response models for AI-orchestrated project management
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ...models.project_orchestration import (
    OrchestrationStatus, CoordinationPattern, JourneyStage,
    TouchpointType, AgentRole
)


# ===================== Base Schemas =====================

class OrchestrationConfigSchema(BaseModel):
    """Configuration for project orchestration"""
    coordination_pattern: CoordinationPattern = CoordinationPattern.HIERARCHICAL
    auto_agent_assignment: bool = True
    real_time_monitoring: bool = True
    max_concurrent_agents: int = Field(default=5, ge=1, le=20)
    optimization_frequency_hours: int = Field(default=24, ge=1, le=168)
    cost_optimization_enabled: bool = True
    quality_gates_enabled: bool = True


class AgentAssignmentConfigSchema(BaseModel):
    """Configuration for agent assignment"""
    agent_name: str = Field(..., min_length=1, max_length=100)
    role: AgentRole = AgentRole.CONTRIBUTOR
    assignment_reason: Optional[str] = None
    expected_contribution: Optional[str] = None
    tools_enabled: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    config_overrides: Dict[str, Any] = Field(default_factory=dict)


# ===================== Request Schemas =====================

class EnhancedProjectCreateRequest(BaseModel):
    """Request for creating an AI-orchestrated project"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_type: str = Field(..., description="Type of project for agent selection")
    
    # Requirements and constraints
    requirements: List[str] = Field(..., min_items=1, description="Project requirements")
    constraints: List[str] = Field(default_factory=list, description="Project constraints")
    success_criteria: List[str] = Field(default_factory=list, description="Success criteria")
    
    # Budget and timeline
    budget: Optional[float] = Field(None, ge=0)
    timeline_days: Optional[int] = Field(None, ge=1)
    
    # Orchestration configuration
    orchestration_config: OrchestrationConfigSchema = Field(default_factory=OrchestrationConfigSchema)
    primary_agent: Optional[str] = None  # Auto-selected if not provided
    
    # Context and metadata
    context: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    # User context
    user_id: Optional[str] = None
    client_id: Optional[str] = None


class AgentAssignmentRequest(BaseModel):
    """Request for assigning agents to project"""
    orchestration_id: str
    agent_assignments: List[AgentAssignmentConfigSchema]
    replace_existing: bool = False


class JourneyStageUpdateRequest(BaseModel):
    """Request for updating journey stage"""
    orchestration_id: str
    stage_name: JourneyStage
    status: str = Field(..., pattern="^(pending|active|completed|blocked|skipped)$")
    progress_percentage: float = Field(..., ge=0, le=100)
    notes: Optional[str] = None
    deliverables: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)


class TouchpointCreateRequest(BaseModel):
    """Request for creating a project touchpoint"""
    orchestration_id: str
    touchpoint_type: TouchpointType
    title: str = Field(..., min_length=1, max_length=500)
    summary: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    duration_minutes: Optional[int] = Field(None, ge=0)
    key_decisions: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    satisfaction_score: Optional[float] = Field(None, ge=0, le=1)
    impact_level: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    tags: List[str] = Field(default_factory=list)


class ConversationCreateRequest(BaseModel):
    """Request for creating agent conversation"""
    orchestration_id: str
    topic: str = Field(..., min_length=1, max_length=500)
    purpose: str = Field(default="planning")
    participants: List[str] = Field(..., min_items=1)
    initial_message: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)


# ===================== Response Schemas =====================

class AgentAssignmentResponse(BaseModel):
    """Response for agent assignment"""
    id: str
    agent_name: str
    agent_role: AgentRole
    assignment_date: datetime
    active: bool
    tasks_completed: int
    tasks_assigned: int
    efficiency_score: float
    collaboration_score: float
    quality_score: float
    cost_incurred: float
    last_active: Optional[datetime]
    
    class Config:
        from_attributes = True


class JourneyStageResponse(BaseModel):
    """Response for journey stage"""
    id: str
    stage_name: JourneyStage
    stage_order: int
    status: str
    progress_percentage: float
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    estimated_duration_days: Optional[int]
    actual_duration_days: Optional[int]
    primary_agents: List[str]
    expected_deliverables: List[str]
    actual_deliverables: List[str]
    satisfaction_score: float
    efficiency_score: float
    blockers: List[str]
    stage_notes: Optional[str]
    
    class Config:
        from_attributes = True


class TouchpointResponse(BaseModel):
    """Response for touchpoint"""
    id: str
    touchpoint_type: TouchpointType
    title: Optional[str]
    initiated_by: str
    participants: List[str]
    interaction_date: datetime
    duration_minutes: Optional[int]
    summary: Optional[str]
    key_decisions: List[str]
    action_items: List[str]
    sentiment_score: float
    satisfaction_score: float
    impact_level: str
    related_stage: Optional[JourneyStage]
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Response for conversation"""
    id: str
    conversation_id: str
    topic: Optional[str]
    purpose: Optional[str]
    participants: List[str]
    status: str
    message_count: int
    turn_count: int
    efficiency_score: float
    collaboration_quality: float
    total_cost: float
    start_time: datetime
    end_time: Optional[datetime]
    conversation_summary: Optional[str]
    decisions_made: List[str]
    action_items: List[str]
    
    class Config:
        from_attributes = True


class ProjectOrchestrationResponse(BaseModel):
    """Main response for project orchestration"""
    id: str
    project_id: str
    orchestration_enabled: bool
    primary_agent: str
    coordination_pattern: CoordinationPattern
    orchestration_status: OrchestrationStatus
    current_stage: JourneyStage
    
    # Performance metrics
    ai_efficiency_score: float
    agent_collaboration_score: float
    cost_per_deliverable: float
    optimization_score: float
    satisfaction_score: float
    
    # Journey tracking
    journey_start_date: datetime
    touchpoint_count: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_optimization: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProjectOrchestrationDetailResponse(ProjectOrchestrationResponse):
    """Detailed response with relationships"""
    agent_assignments: List[AgentAssignmentResponse]
    journey_stages: List[JourneyStageResponse]
    recent_touchpoints: List[TouchpointResponse]
    active_conversations: List[ConversationResponse]


# ===================== Analytics Schemas =====================

class OrchestrationMetricsResponse(BaseModel):
    """Orchestration performance metrics"""
    orchestration_id: str
    
    # Performance metrics
    overall_efficiency: float
    agent_utilization: float
    cost_efficiency: float
    timeline_efficiency: float
    quality_score: float
    
    # Agent collaboration
    collaboration_score: float
    conflict_resolution_score: float
    knowledge_sharing_score: float
    
    # Journey analytics
    stage_completion_rate: float
    average_stage_duration: float
    touchpoint_effectiveness: float
    satisfaction_trend: List[Dict[str, Any]]
    
    # Cost analytics
    total_cost: float
    cost_per_hour: float
    cost_by_agent: Dict[str, float]
    cost_optimization_savings: float
    
    # Recommendations
    optimization_recommendations: List[str]
    agent_rebalancing_suggestions: List[Dict[str, Any]]
    process_improvements: List[str]
    
    # Analysis metadata
    analysis_period_start: datetime
    analysis_period_end: datetime
    calculated_at: datetime


class AgentCollaborationMetricsResponse(BaseModel):
    """Agent collaboration analytics"""
    orchestration_id: str
    
    # Collaboration matrix
    agent_pairs: List[Dict[str, Any]]
    synergy_scores: Dict[str, float]
    conflict_scores: Dict[str, float]
    
    # Performance insights
    most_effective_pairs: List[Dict[str, Any]]
    problematic_combinations: List[Dict[str, Any]]
    optimization_opportunities: List[str]
    
    # Recommendations
    rebalancing_suggestions: List[Dict[str, Any]]
    skill_gap_analysis: List[str]
    training_recommendations: List[str]


class ProjectJourneyAnalyticsResponse(BaseModel):
    """CRM-style journey analytics"""
    orchestration_id: str
    
    # Journey overview
    current_stage: JourneyStage
    completion_percentage: float
    estimated_completion_date: Optional[datetime]
    
    # Stage analytics
    stage_progression: List[Dict[str, Any]]
    stage_duration_analysis: Dict[str, Any]
    bottleneck_analysis: List[str]
    
    # Touchpoint analytics
    touchpoint_summary: Dict[str, int]
    interaction_frequency: Dict[str, float]
    satisfaction_trends: List[Dict[str, Any]]
    
    # Predictive analytics
    risk_factors: List[str]
    success_probability: float
    recommended_interventions: List[str]


# ===================== Optimization Schemas =====================

class OptimizationRequest(BaseModel):
    """Request for project optimization"""
    orchestration_id: str
    optimization_type: str = Field(..., pattern="^(performance|cost|timeline|quality|all)$")
    constraints: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class OptimizationResponse(BaseModel):
    """Response for optimization recommendations"""
    orchestration_id: str
    optimization_type: str
    
    # Current state analysis
    current_performance: Dict[str, float]
    identified_issues: List[str]
    improvement_opportunities: List[str]
    
    # Recommendations
    agent_reassignments: List[Dict[str, Any]]
    process_optimizations: List[str]
    resource_adjustments: List[Dict[str, Any]]
    timeline_adjustments: List[Dict[str, Any]]
    
    # Predicted impacts
    expected_improvements: Dict[str, float]
    implementation_effort: str
    estimated_savings: Dict[str, float]
    
    # Implementation plan
    implementation_steps: List[Dict[str, Any]]
    rollback_plan: List[str]
    success_metrics: List[str]
    
    # Analysis metadata
    analysis_date: datetime
    confidence_score: float
    valid_until: datetime


# ===================== Streaming Schemas =====================

class StreamingUpdateResponse(BaseModel):
    """Real-time streaming update"""
    orchestration_id: str
    update_type: str  # status, conversation, metric, error
    timestamp: datetime
    data: Dict[str, Any]
    sequence_number: int


class ConversationStreamResponse(BaseModel):
    """Streaming conversation update"""
    conversation_id: str
    orchestration_id: str
    participant: str
    message_type: str  # text, action, decision, error
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)