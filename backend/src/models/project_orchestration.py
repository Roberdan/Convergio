"""
Enhanced Project Orchestration Models
AI-orchestrated project management with CRM-style journey tracking
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, Float,
    ForeignKey, JSON, Enum as SQLEnum, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.database import Base


class OrchestrationStatus(str, Enum):
    """Status of project orchestration"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    OPTIMIZING = "optimizing"
    COMPLETED = "completed"
    FAILED = "failed"


class CoordinationPattern(str, Enum):
    """Agent coordination patterns"""
    HIERARCHICAL = "hierarchical"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    SWARM = "swarm"
    HYBRID = "hybrid"


class JourneyStage(str, Enum):
    """CRM-style project journey stages"""
    DISCOVERY = "discovery"
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    DELIVERY = "delivery"
    CLOSURE = "closure"


class TouchpointType(str, Enum):
    """Types of project touchpoints"""
    AGENT_INTERACTION = "agent_interaction"
    CLIENT_CHECKIN = "client_checkin"
    MILESTONE_REVIEW = "milestone_review"
    STATUS_UPDATE = "status_update"
    DECISION_POINT = "decision_point"
    QUALITY_GATE = "quality_gate"
    ESCALATION = "escalation"


class AgentRole(str, Enum):
    """Agent roles in project execution"""
    PRIMARY = "primary"
    CONTRIBUTOR = "contributor"
    CONSULTANT = "consultant"
    REVIEWER = "reviewer"
    OBSERVER = "observer"


class ProjectOrchestration(Base):
    """Enhanced project model with AI orchestration capabilities"""
    __tablename__ = 'project_orchestrations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, unique=True)
    
    # Orchestration configuration
    orchestration_enabled = Column(Boolean, default=True, nullable=False)
    primary_agent = Column(String(100), nullable=False)
    coordination_pattern = Column(SQLEnum(CoordinationPattern), default=CoordinationPattern.HIERARCHICAL)
    auto_agent_assignment = Column(Boolean, default=True)
    real_time_monitoring = Column(Boolean, default=True)
    
    # Current state
    orchestration_status = Column(SQLEnum(OrchestrationStatus), default=OrchestrationStatus.INITIALIZING)
    current_stage = Column(SQLEnum(JourneyStage), default=JourneyStage.DISCOVERY)
    active_conversation_id = Column(String(255))
    
    # Performance metrics
    ai_efficiency_score = Column(Float, default=0.0)
    agent_collaboration_score = Column(Float, default=0.0)
    cost_per_deliverable = Column(Float, default=0.0)
    optimization_score = Column(Float, default=0.0)
    
    # Journey tracking
    journey_start_date = Column(DateTime, default=datetime.utcnow)
    stage_progression = Column(JSON, default=list)  # Track stage transitions
    touchpoint_count = Column(Integer, default=0)
    satisfaction_score = Column(Float, default=0.0)
    
    # Configuration and context
    orchestration_config = Column(JSON, default=dict)
    context_data = Column(JSON, default=dict)
    constraints = Column(JSON, default=list)
    success_criteria = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_optimization = Column(DateTime)
    
    # Relationships
    project = relationship("Project", backref=backref("orchestration", uselist=False))
    agent_assignments = relationship("ProjectAgentAssignment", back_populates="orchestration", cascade="all, delete-orphan")
    journey_stages = relationship("ProjectJourneyStage", back_populates="orchestration", cascade="all, delete-orphan")
    touchpoints = relationship("ProjectTouchpoint", back_populates="orchestration", cascade="all, delete-orphan")
    conversations = relationship("ProjectConversation", back_populates="orchestration", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_orchestration_status', 'orchestration_status'),
        Index('idx_project_orchestration_stage', 'current_stage'),
        Index('idx_project_orchestration_agent', 'primary_agent'),
        CheckConstraint('ai_efficiency_score >= 0 AND ai_efficiency_score <= 1'),
        CheckConstraint('agent_collaboration_score >= 0 AND agent_collaboration_score <= 1'),
        CheckConstraint('satisfaction_score >= 0 AND satisfaction_score <= 1'),
    )


class ProjectAgentAssignment(Base):
    """Agent assignments for orchestrated projects"""
    __tablename__ = 'project_agent_assignments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchestration_id = Column(UUID(as_uuid=True), ForeignKey('project_orchestrations.id'), nullable=False)
    agent_name = Column(String(100), nullable=False)
    agent_role = Column(SQLEnum(AgentRole), default=AgentRole.CONTRIBUTOR)
    
    # Assignment details
    assignment_date = Column(DateTime, default=datetime.utcnow)
    assignment_reason = Column(Text)
    expected_contribution = Column(Text)
    active = Column(Boolean, default=True)
    
    # Performance tracking
    tasks_completed = Column(Integer, default=0)
    tasks_assigned = Column(Integer, default=0)
    efficiency_score = Column(Float, default=0.0)
    collaboration_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    
    # Cost tracking
    cost_incurred = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    api_calls_made = Column(Integer, default=0)
    
    # Agent-specific configuration
    agent_config = Column(JSON, default=dict)
    tools_enabled = Column(JSON, default=list)
    permissions = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime)
    
    # Relationships
    orchestration = relationship("ProjectOrchestration", back_populates="agent_assignments")
    
    # Indexes
    __table_args__ = (
        Index('idx_agent_assignment_orchestration', 'orchestration_id'),
        Index('idx_agent_assignment_name', 'agent_name'),
        Index('idx_agent_assignment_role', 'agent_role'),
        Index('idx_agent_assignment_active', 'active'),
        CheckConstraint('efficiency_score >= 0 AND efficiency_score <= 1'),
        CheckConstraint('collaboration_score >= 0 AND collaboration_score <= 1'),
        CheckConstraint('quality_score >= 0 AND quality_score <= 1'),
    )


class ProjectJourneyStage(Base):
    """CRM-style journey stages for projects"""
    __tablename__ = 'project_journey_stages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchestration_id = Column(UUID(as_uuid=True), ForeignKey('project_orchestrations.id'), nullable=False)
    stage_name = Column(SQLEnum(JourneyStage), nullable=False)
    stage_order = Column(Integer, nullable=False)
    
    # Stage execution details
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    estimated_duration_days = Column(Integer)
    actual_duration_days = Column(Integer)
    
    # Status and progress
    status = Column(String(50), default='pending')  # pending, active, completed, blocked, skipped
    progress_percentage = Column(Float, default=0.0)
    completion_confidence = Column(Float, default=0.0)
    
    # Agent involvement
    primary_agents = Column(JSON, default=list)  # List of agent names
    contributing_agents = Column(JSON, default=list)
    agent_interactions = Column(Integer, default=0)
    
    # Deliverables and outcomes
    expected_deliverables = Column(JSON, default=list)
    actual_deliverables = Column(JSON, default=list)
    deliverable_quality_score = Column(Float, default=0.0)
    
    # Quality and satisfaction metrics
    satisfaction_score = Column(Float, default=0.0)
    efficiency_score = Column(Float, default=0.0)
    cost_efficiency = Column(Float, default=0.0)
    
    # Issues and risks
    blockers = Column(JSON, default=list)
    risks_identified = Column(JSON, default=list)
    mitigation_actions = Column(JSON, default=list)
    
    # Metadata
    stage_notes = Column(Text)
    lessons_learned = Column(Text)
    improvement_suggestions = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orchestration = relationship("ProjectOrchestration", back_populates="journey_stages")
    
    # Indexes
    __table_args__ = (
        Index('idx_journey_stage_orchestration', 'orchestration_id'),
        Index('idx_journey_stage_name', 'stage_name'),
        Index('idx_journey_stage_order', 'stage_order'),
        Index('idx_journey_stage_status', 'status'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100'),
        CheckConstraint('satisfaction_score >= 0 AND satisfaction_score <= 1'),
        CheckConstraint('efficiency_score >= 0 AND efficiency_score <= 1'),
    )


class ProjectTouchpoint(Base):
    """CRM-style touchpoints for project interactions"""
    __tablename__ = 'project_touchpoints'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchestration_id = Column(UUID(as_uuid=True), ForeignKey('project_orchestrations.id'), nullable=False)
    touchpoint_type = Column(SQLEnum(TouchpointType), nullable=False)
    
    # Interaction details
    initiated_by = Column(String(100), nullable=False)  # agent_name or user_id
    participants = Column(JSON, default=list)  # List of participants
    interaction_date = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer)
    channel = Column(String(50))  # conversation, email, meeting, etc.
    
    # Content and context
    title = Column(String(500))
    summary = Column(Text)
    key_decisions = Column(JSON, default=list)
    action_items = Column(JSON, default=list)
    follow_up_required = Column(Boolean, default=False)
    
    # Sentiment and quality
    sentiment_score = Column(Float, default=0.0)  # -1 to 1
    satisfaction_score = Column(Float, default=0.0)  # 0 to 1
    productivity_score = Column(Float, default=0.0)  # 0 to 1
    
    # Relationships and references
    related_stage = Column(SQLEnum(JourneyStage))
    related_tasks = Column(JSON, default=list)  # Task IDs
    related_agents = Column(JSON, default=list)  # Agent names
    
    # Impact and outcomes
    impact_level = Column(String(20), default='medium')  # low, medium, high, critical
    outcomes_achieved = Column(JSON, default=list)
    issues_raised = Column(JSON, default=list)
    
    # Metadata
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orchestration = relationship("ProjectOrchestration", back_populates="touchpoints")
    
    # Indexes
    __table_args__ = (
        Index('idx_touchpoint_orchestration', 'orchestration_id'),
        Index('idx_touchpoint_type', 'touchpoint_type'),
        Index('idx_touchpoint_date', 'interaction_date'),
        Index('idx_touchpoint_initiator', 'initiated_by'),
        Index('idx_touchpoint_stage', 'related_stage'),
        CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1'),
        CheckConstraint('satisfaction_score >= 0 AND satisfaction_score <= 1'),
        CheckConstraint('productivity_score >= 0 AND productivity_score <= 1'),
    )


class ProjectConversation(Base):
    """Agent conversations within projects"""
    __tablename__ = 'project_conversations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchestration_id = Column(UUID(as_uuid=True), ForeignKey('project_orchestrations.id'), nullable=False)
    conversation_id = Column(String(255), nullable=False)  # External conversation ID
    
    # Conversation metadata
    topic = Column(String(500))
    purpose = Column(String(100))  # planning, problem_solving, status_update, etc.
    participants = Column(JSON, default=list)  # List of agent names
    
    # Status and progress
    status = Column(String(50), default='active')  # active, completed, paused, terminated
    message_count = Column(Integer, default=0)
    turn_count = Column(Integer, default=0)
    
    # Performance metrics
    efficiency_score = Column(Float, default=0.0)
    collaboration_quality = Column(Float, default=0.0)
    outcome_quality = Column(Float, default=0.0)
    
    # Cost tracking
    total_cost = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    api_calls_made = Column(Integer, default=0)
    
    # Outcomes and deliverables
    decisions_made = Column(JSON, default=list)
    action_items = Column(JSON, default=list)
    deliverables_produced = Column(JSON, default=list)
    issues_resolved = Column(JSON, default=list)
    
    # Timing
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    conversation_summary = Column(Text)
    key_insights = Column(JSON, default=list)
    improvement_suggestions = Column(JSON, default=list)
    
    # Relationships
    orchestration = relationship("ProjectOrchestration", back_populates="conversations")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_orchestration', 'orchestration_id'),
        Index('idx_conversation_id', 'conversation_id'),
        Index('idx_conversation_status', 'status'),
        Index('idx_conversation_start', 'start_time'),
        CheckConstraint('efficiency_score >= 0 AND efficiency_score <= 1'),
        CheckConstraint('collaboration_quality >= 0 AND collaboration_quality <= 1'),
        CheckConstraint('outcome_quality >= 0 AND outcome_quality <= 1'),
    )


class AgentCollaborationMetric(Base):
    """Metrics for agent collaboration patterns"""
    __tablename__ = 'agent_collaboration_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchestration_id = Column(UUID(as_uuid=True), ForeignKey('project_orchestrations.id'), nullable=False)
    
    # Agent pair or group
    primary_agent = Column(String(100), nullable=False)
    secondary_agent = Column(String(100))  # For pair metrics
    agent_group = Column(JSON, default=list)  # For group metrics
    
    # Collaboration metrics
    interaction_frequency = Column(Float, default=0.0)
    synergy_score = Column(Float, default=0.0)
    conflict_score = Column(Float, default=0.0)
    efficiency_multiplier = Column(Float, default=1.0)
    
    # Performance outcomes
    joint_tasks_completed = Column(Integer, default=0)
    average_task_quality = Column(Float, default=0.0)
    collaboration_duration_hours = Column(Float, default=0.0)
    
    # Analysis period
    measurement_start = Column(DateTime, nullable=False)
    measurement_end = Column(DateTime, nullable=False)
    
    # Insights and recommendations
    collaboration_insights = Column(JSON, default=list)
    optimization_suggestions = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_collaboration_orchestration', 'orchestration_id'),
        Index('idx_collaboration_agents', 'primary_agent', 'secondary_agent'),
        Index('idx_collaboration_period', 'measurement_start', 'measurement_end'),
        CheckConstraint('synergy_score >= 0 AND synergy_score <= 1'),
        CheckConstraint('conflict_score >= 0 AND conflict_score <= 1'),
        CheckConstraint('average_task_quality >= 0 AND average_task_quality <= 1'),
    )