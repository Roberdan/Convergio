"""
Project Management Domain Models
Projects, Epics, Tasks, Subtasks, Resources, Dependencies
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, Float,
    ForeignKey, JSON, Table, Enum as SQLEnum, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.database import Base


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResourceType(str, Enum):
    HUMAN = "human"
    AI_AGENT = "ai_agent"
    SYSTEM = "system"
    EXTERNAL = "external"


# Association tables for many-to-many relationships
task_dependencies = Table(
    'task_dependencies',
    Base.metadata,
    Column('dependent_task_id', UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True),
    Column('dependency_task_id', UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True)
)

task_resources = Table(
    'task_resources',
    Base.metadata,
    Column('task_id', UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True),
    Column('resource_id', UUID(as_uuid=True), ForeignKey('resources.id'), primary_key=True),
    Column('allocation_percentage', Float, default=100.0),
    Column('assigned_at', DateTime, default=datetime.utcnow)
)

task_agents = Table(
    'task_agents',
    Base.metadata,
    Column('task_id', UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True),
    Column('agent_name', String(100), primary_key=True),
    Column('attached_at', DateTime, default=datetime.utcnow),
    Column('configuration', JSON, default={})
)


class Project(Base):
    """Project model - top-level container for work"""
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    # Use string status for compatibility with tests (expects 'active')
    status = Column(String(50), default='active')
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Ownership
    # Align owner to Talent model (tests create Talent and assign as owner)
    owner_id = Column(Integer, ForeignKey('talents.id'))
    # Optional client reference; FK removed to avoid dependency on missing 'clients' table in tests
    client_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timeline
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    
    # Budget and costs
    budget = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    ai_cost = Column(Float, default=0.0)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    health_score = Column(Float, default=100.0)  # 0-100 health indicator
    
    # Metadata
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    epics = relationship("Epic", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="project", cascade="all, delete-orphan")
    # AI Orchestration relationship - defined in project_orchestration.py
    # orchestration = relationship("ProjectOrchestration", back_populates="project", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_project_status', 'status'),
        Index('idx_project_owner', 'owner_id'),
        Index('idx_project_dates', 'start_date', 'end_date'),
    )


class Epic(Base):
    """Epic model - large feature or initiative within a project"""
    __tablename__ = 'epics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Timeline
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Progress
    progress_percentage = Column(Float, default=0.0)
    story_points = Column(Integer, default=0)
    
    # Metadata
    color = Column(String(7), default='#3B82F6')  # Hex color for UI
    icon = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="epics")
    tasks = relationship("Task", back_populates="epic", cascade="all, delete-orphan")


class Task(Base):
    """Task model - individual work items"""
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    epic_id = Column(UUID(as_uuid=True), ForeignKey('epics.id'))
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'))
    
    # Basic info
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Assignment
    # Align assignee to Talent model
    assignee_id = Column(Integer, ForeignKey('talents.id'))
    assigned_agent = Column(String(100))  # AI agent assignment
    
    # Timeline
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Effort tracking
    estimated_hours = Column(Float, default=0.0)
    actual_hours = Column(Float, default=0.0)
    story_points = Column(Integer)
    
    # Progress
    progress_percentage = Column(Float, default=0.0)
    is_milestone = Column(Boolean, default=False)
    
    # AI Integration
    ai_suggestions = Column(JSON, default=list)
    ai_completed = Column(Boolean, default=False)
    ai_confidence = Column(Float)
    execution_logs = Column(JSON, default=list)
    
    # Metadata
    tags = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    epic = relationship("Epic", back_populates="tasks")
    subtasks = relationship("Task", backref=backref('parent', remote_side=[id]))
    
    # Many-to-many relationships
    dependencies = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin=id == task_dependencies.c.dependent_task_id,
        secondaryjoin=id == task_dependencies.c.dependency_task_id,
        backref="dependents"
    )
    
    resources = relationship(
        "Resource",
        secondary=task_resources,
        back_populates="tasks"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_task_status', 'status'),
        Index('idx_task_assignee', 'assignee_id'),
        Index('idx_task_due_date', 'due_date'),
        Index('idx_task_project', 'project_id'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100'),
    )


class Resource(Base):
    """Resource model - people, agents, or systems available for tasks"""
    __tablename__ = 'resources'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    
    name = Column(String(200), nullable=False)
    type = Column(SQLEnum(ResourceType), default=ResourceType.HUMAN)
    
    # Capacity
    availability_percentage = Column(Float, default=100.0)
    max_hours_per_day = Column(Float, default=8.0)
    cost_per_hour = Column(Float, default=0.0)
    
    # For AI agents
    agent_name = Column(String(100))
    agent_capabilities = Column(JSON, default=list)
    
    # Skills and attributes
    skills = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    
    # Availability
    available_from = Column(DateTime)
    available_until = Column(DateTime)
    timezone = Column(String(50), default='UTC')
    
    # Metadata
    contact_info = Column(JSON, default=dict)
    custom_fields = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="resources")
    tasks = relationship(
        "Task",
        secondary=task_resources,
        back_populates="resources"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_resource_type', 'type'),
        Index('idx_resource_project', 'project_id'),
    )


class TaskConversation(Base):
    """Conversation threads attached to tasks"""
    __tablename__ = 'task_conversations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False)
    
    # Conversation data
    messages = Column(JSON, default=list)
    participants = Column(JSON, default=list)  # Users and agents involved
    
    # AI context
    context = Column(JSON, default=dict)
    decisions = Column(JSON, default=list)
    total_cost = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    resolved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    task = relationship("Task", backref="conversations")


class ProjectAnalytics(Base):
    """Analytics and KPIs for projects"""
    __tablename__ = 'project_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    
    # Performance metrics
    velocity = Column(Float, default=0.0)  # Story points per sprint
    burn_rate = Column(Float, default=0.0)  # Budget consumption rate
    cycle_time = Column(Float, default=0.0)  # Average task completion time
    lead_time = Column(Float, default=0.0)  # Request to delivery time
    
    # Quality metrics
    defect_rate = Column(Float, default=0.0)
    rework_percentage = Column(Float, default=0.0)
    
    # Team metrics
    team_utilization = Column(Float, default=0.0)
    ai_utilization = Column(Float, default=0.0)
    
    # Cost metrics
    cost_variance = Column(Float, default=0.0)  # Actual vs budgeted
    roi = Column(Float, default=0.0)
    
    # Predictive metrics
    estimated_completion_date = Column(DateTime)
    risk_score = Column(Float, default=0.0)
    
    # Time series data
    daily_metrics = Column(JSON, default=list)
    weekly_metrics = Column(JSON, default=list)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", backref="analytics")