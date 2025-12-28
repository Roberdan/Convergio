"""
💰 Convergio - Cost Tracking Database Models
Comprehensive cost tracking for AI model usage across all providers
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    DECIMAL, JSON, Boolean, DateTime, Float, Index, Integer,
    String, Text, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Provider(str, Enum):
    """AI Provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GOOGLE = "google"
    AZURE = "azure"
    AWS_BEDROCK = "aws_bedrock"
    CUSTOM = "custom"


class CostStatus(str, Enum):
    """Cost tracking status"""
    HEALTHY = "healthy"
    MODERATE = "moderate"
    WARNING = "warning"
    EXCEEDED = "exceeded"
    ERROR = "error"


class CostTracking(Base):
    """Main cost tracking table for all AI interactions"""
    __tablename__ = "cost_tracking"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Session and conversation tracking
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    conversation_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    turn_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Agent information
    agent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Provider and model details
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Token usage
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Cost calculations (stored as DECIMAL for precision)
    input_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False)
    output_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False)
    total_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, index=True)
    
    # Additional request metadata
    request_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # chat, completion, embedding, search
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional metadata JSON for tracking
    request_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_cost_tracking_date', 'created_at'),
        Index('idx_cost_tracking_session_conversation', 'session_id', 'conversation_id'),
        Index('idx_cost_tracking_provider_model', 'provider', 'model'),
        Index('idx_cost_tracking_agent', 'agent_id'),
        {"extend_existing": True},
    )


class CostSession(Base):
    """Session-level cost aggregation"""
    __tablename__ = "cost_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    
    # User information (if available)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Aggregated costs
    total_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_interactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Provider breakdown (JSON)
    provider_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    model_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    agent_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Session status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=CostStatus.HEALTHY.value)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tracking_records = relationship("CostTracking", 
                                   foreign_keys="[CostTracking.session_id]",
                                   primaryjoin="CostSession.session_id == CostTracking.session_id",
                                   viewonly=True)

    __table_args__ = ({"extend_existing": True},)


class DailyCostSummary(Base):
    """Daily cost aggregation for reporting"""
    __tablename__ = "daily_cost_summary"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, unique=True, index=True)
    
    # Total costs
    total_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_interactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Provider breakdown
    openai_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    anthropic_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    perplexity_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    other_cost_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    
    # Detailed breakdowns (JSON)
    provider_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    model_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    agent_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    hourly_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Statistics
    avg_cost_per_interaction: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    avg_tokens_per_interaction: Mapped[Float] = mapped_column(Float, nullable=False, default=0)
    peak_hour_cost: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=0)
    peak_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Budget tracking
    daily_budget_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False, default=50.0)
    budget_utilization_percent: Mapped[Float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=CostStatus.HEALTHY.value)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = ({"extend_existing": True},)


class ProviderPricing(Base):
    """Current pricing for different providers and models"""
    __tablename__ = "provider_pricing"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Pricing per 1K tokens (stored as DECIMAL for precision)
    input_price_per_1k: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False)
    output_price_per_1k: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False)
    
    # Additional pricing (for search APIs)
    price_per_request: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6), nullable=True)
    
    # Model capabilities
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    context_window: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Effective dates
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now()
    )
    
    __table_args__ = (
        UniqueConstraint('provider', 'model', 'effective_from', name='uq_provider_model_date'),
        Index('idx_provider_pricing_active', 'provider', 'model', 'is_active'),
        {"extend_existing": True},
    )


class CostAlert(Base):
    """Cost alerts and notifications"""
    __tablename__ = "cost_alerts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Alert details
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # daily_limit, session_limit, spike, etc.
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # info, warning, critical
    
    # Context
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Alert data
    current_value: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(DECIMAL(10, 6), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    
    __table_args__ = (
        Index('idx_cost_alerts_unresolved', 'is_resolved', 'severity'),
        Index('idx_cost_alerts_date', 'created_at'),
        {"extend_existing": True},
    )