"""
Multi-Tenant SaaS Model with Billing Integration
Complete tenant isolation and subscription management
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, Numeric, Date,
    ForeignKey, JSON, Enum as SQLEnum, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.database import Base


class TenantStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SubscriptionPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingPeriod(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Tenant(Base):
    """Main tenant model for multi-tenancy"""
    __tablename__ = 'tenants'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(200), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)  # URL-friendly identifier
    display_name = Column(String(200))
    description = Column(Text)
    
    # Contact information
    email = Column(String(200), nullable=False)
    phone = Column(String(50))
    website = Column(String(200))
    
    # Address
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    
    # Tenant configuration
    domain = Column(String(200), unique=True)  # Custom domain
    subdomain = Column(String(100), unique=True)  # {subdomain}.convergio.ai
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    currency = Column(String(3), default='USD')
    
    # Status and lifecycle
    status = Column(SQLEnum(TenantStatus), default=TenantStatus.TRIAL)
    trial_ends_at = Column(DateTime)
    activated_at = Column(DateTime)
    suspended_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    # Subscription
    subscription_plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    billing_period = Column(SQLEnum(BillingPeriod), default=BillingPeriod.MONTHLY)
    subscription_ends_at = Column(DateTime)
    
    # Stripe integration
    stripe_customer_id = Column(String(100), unique=True)
    stripe_subscription_id = Column(String(100))
    payment_method_id = Column(String(100))
    
    # Usage limits (based on plan)
    max_users = Column(Integer, default=5)
    max_projects = Column(Integer, default=10)
    max_workflows = Column(Integer, default=100)
    max_api_calls = Column(Integer, default=10000)
    max_storage_gb = Column(Integer, default=10)
    max_ai_tokens = Column(Integer, default=100000)
    
    # Current usage
    current_users = Column(Integer, default=0)
    current_projects = Column(Integer, default=0)
    current_workflows = Column(Integer, default=0)
    current_api_calls = Column(Integer, default=0)
    current_storage_gb = Column(Numeric(10, 2), default=0)
    current_ai_tokens = Column(Integer, default=0)
    
    # Features flags
    features = Column(JSON, default=dict)
    # Example: {
    #   "advanced_analytics": true,
    #   "custom_agents": false,
    #   "api_access": true,
    #   "sso": false,
    #   "white_label": false
    # }
    
    # Metadata
    settings = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="tenant", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("TenantAuditLog", back_populates="tenant", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_tenant_status', 'status'),
        Index('idx_tenant_slug', 'slug'),
        Index('idx_tenant_subdomain', 'subdomain'),
        Index('idx_tenant_stripe', 'stripe_customer_id'),
    )
    
    def is_active(self) -> bool:
        """Check if tenant is active"""
        return self.status == TenantStatus.ACTIVE
    
    def can_add_user(self) -> bool:
        """Check if tenant can add more users"""
        return self.current_users < self.max_users
    
    def can_create_project(self) -> bool:
        """Check if tenant can create more projects"""
        return self.current_projects < self.max_projects
    
    def get_usage_percentage(self, resource: str) -> float:
        """Get usage percentage for a resource"""
        current = getattr(self, f"current_{resource}", 0)
        max_val = getattr(self, f"max_{resource}", 1)
        return (current / max_val) * 100 if max_val > 0 else 0


class TenantUser(Base):
    """Users within a tenant"""
    __tablename__ = 'tenant_users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Role within tenant
    role = Column(String(50), default='member')  # owner, admin, member, viewer
    
    # Permissions
    permissions = Column(JSON, default=list)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_primary_owner = Column(Boolean, default=False)
    
    # Invitation
    invited_by = Column(UUID(as_uuid=True))
    invited_at = Column(DateTime)
    accepted_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_user'),
        Index('idx_tenant_user', 'tenant_id', 'user_id'),
    )


class SubscriptionPlanDefinition(Base):
    """Definition of available subscription plans"""
    __tablename__ = 'subscription_plans'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200))
    description = Column(Text)
    
    # Pricing
    monthly_price = Column(Numeric(10, 2), default=0)
    yearly_price = Column(Numeric(10, 2), default=0)
    currency = Column(String(3), default='USD')
    
    # Stripe product/price IDs
    stripe_product_id = Column(String(100))
    stripe_monthly_price_id = Column(String(100))
    stripe_yearly_price_id = Column(String(100))
    
    # Limits
    max_users = Column(Integer, default=5)
    max_projects = Column(Integer, default=10)
    max_workflows = Column(Integer, default=100)
    max_api_calls = Column(Integer, default=10000)
    max_storage_gb = Column(Integer, default=10)
    max_ai_tokens = Column(Integer, default=100000)
    
    # Features
    features = Column(JSON, default=dict)
    
    # Display
    is_popular = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Invoice(Base):
    """Billing invoices for tenants"""
    __tablename__ = 'invoices'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    
    # Invoice details
    invoice_number = Column(String(50), unique=True, nullable=False)
    stripe_invoice_id = Column(String(100), unique=True)
    
    # Billing period
    billing_period_start = Column(Date)
    billing_period_end = Column(Date)
    
    # Amounts
    subtotal = Column(Numeric(10, 2), default=0)
    tax = Column(Numeric(10, 2), default=0)
    discount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), default=0)
    currency = Column(String(3), default='USD')
    
    # Status
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    due_date = Column(Date)
    paid_at = Column(DateTime)
    
    # Line items
    line_items = Column(JSON, default=list)
    # Format: [
    #   {
    #     "description": "Professional Plan - Monthly",
    #     "quantity": 1,
    #     "unit_price": 99.00,
    #     "total": 99.00
    #   }
    # ]
    
    # Payment
    payment_method = Column(String(50))  # card, bank_transfer, etc.
    payment_details = Column(JSON, default=dict)
    
    # PDF
    pdf_url = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="invoices")
    
    # Indexes
    __table_args__ = (
        Index('idx_invoice_tenant', 'tenant_id'),
        Index('idx_invoice_status', 'status'),
        Index('idx_invoice_due', 'due_date'),
    )


class UsageRecord(Base):
    """Track usage metrics for billing and limits"""
    __tablename__ = 'usage_records'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    
    # Usage type
    resource_type = Column(String(50), nullable=False)  # users, projects, api_calls, etc.
    
    # Usage data
    quantity = Column(Numeric(10, 2), default=0)
    unit = Column(String(20))  # count, GB, tokens, etc.
    
    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Billing
    is_billable = Column(Boolean, default=True)
    unit_price = Column(Numeric(10, 4), default=0)
    total_cost = Column(Numeric(10, 2), default=0)
    
    # Metadata
    extra_data = Column('metadata', JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="usage_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_tenant', 'tenant_id'),
        Index('idx_usage_period', 'period_start', 'period_end'),
        Index('idx_usage_type', 'resource_type'),
    )


class TenantAuditLog(Base):
    """Audit log for tenant activities"""
    __tablename__ = 'tenant_audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    
    # Actor
    user_id = Column(UUID(as_uuid=True))
    user_email = Column(String(200))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Action
    action = Column(String(100), nullable=False)  # login, create_project, delete_user, etc.
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    
    # Details
    description = Column(Text)
    changes = Column(JSON, default=dict)  # before/after values
    extra_data = Column('metadata', JSON, default=dict)
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_tenant', 'tenant_id'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_created', 'created_at'),
    )


# Helper functions

def create_tenant(
    name: str,
    email: str,
    plan: SubscriptionPlan = SubscriptionPlan.FREE,
    **kwargs
) -> Tenant:
    """Create a new tenant"""
    import re
    
    # Generate slug from name
    slug = re.sub(r'[^a-z0-9-]', '-', name.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    
    # Generate subdomain
    subdomain = slug[:50]  # Limit subdomain length
    
    tenant = Tenant(
        name=name,
        slug=slug,
        email=email,
        subdomain=subdomain,
        subscription_plan=plan,
        display_name=kwargs.get('display_name', name),
        **kwargs
    )
    
    # Set trial period for new tenants (FREE plan gets 14 day trial)
    if plan == SubscriptionPlan.FREE:
        from datetime import timedelta
        tenant.trial_ends_at = datetime.utcnow() + timedelta(days=14)
    
    return tenant


def check_tenant_limits(tenant: Tenant, resource: str, quantity: int = 1) -> Tuple[bool, str]:
    """Check if tenant can use more of a resource"""
    current = getattr(tenant, f"current_{resource}", 0)
    max_limit = getattr(tenant, f"max_{resource}", 0)
    
    if current + quantity > max_limit:
        return False, f"Limit exceeded for {resource}. Current: {current}, Max: {max_limit}"
    
    return True, ""


def record_usage(
    tenant_id: str,
    resource_type: str,
    quantity: float,
    unit: str = "count",
    is_billable: bool = False,
    db_session = None
) -> UsageRecord:
    """Record resource usage for a tenant"""
    usage = UsageRecord(
        tenant_id=tenant_id,
        resource_type=resource_type,
        quantity=quantity,
        unit=unit,
        is_billable=is_billable,
        period_start=datetime.utcnow(),
        period_end=datetime.utcnow()
    )
    
    if db_session:
        db_session.add(usage)
    
    return usage