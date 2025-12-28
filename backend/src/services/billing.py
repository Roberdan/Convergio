"""
Billing Service - Stripe integration for SaaS billing
Handles subscriptions, usage metering, and invoicing
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import stripe
import os
import structlog
from pydantic import BaseModel, Field
from enum import Enum

logger = structlog.get_logger()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_dummy")


class BillingPlan(str, Enum):
    """Available billing plans"""
    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingPeriod(str, Enum):
    """Billing periods"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class UsageMetric(str, Enum):
    """Types of usage metrics tracked"""
    API_CALLS = "api_calls"
    AI_TOKENS = "ai_tokens"
    STORAGE_GB = "storage_gb"
    WORKFLOWS_EXECUTED = "workflows_executed"
    AGENTS_INVOKED = "agents_invoked"
    PROJECTS_ACTIVE = "projects_active"
    USERS_ACTIVE = "users_active"


class PlanConfig(BaseModel):
    """Configuration for a billing plan"""
    plan_id: str
    name: str
    description: str
    price_monthly: Decimal
    price_yearly: Decimal
    
    # Quotas
    max_users: int
    max_projects: int
    max_workflows: int
    max_api_calls: int
    max_storage_gb: int
    max_ai_tokens: int
    
    # Features
    features: List[str]
    
    # Overage pricing
    overage_api_calls_per_1000: Decimal = Decimal("0.10")
    overage_ai_tokens_per_1000: Decimal = Decimal("0.02")
    overage_storage_per_gb: Decimal = Decimal("0.10")
    
    # Stripe product/price IDs
    stripe_product_id: Optional[str] = None
    stripe_price_monthly_id: Optional[str] = None
    stripe_price_yearly_id: Optional[str] = None


class UsageRecord(BaseModel):
    """Record of usage for billing"""
    tenant_id: str
    metric: UsageMetric
    quantity: int
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class Invoice(BaseModel):
    """Invoice details"""
    invoice_id: str
    tenant_id: str
    period_start: datetime
    period_end: datetime
    
    subscription_charges: Decimal
    usage_charges: Decimal
    total_amount: Decimal
    
    line_items: List[Dict[str, Any]]
    
    status: str  # draft, open, paid, void
    stripe_invoice_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None


class BillingService:
    """Service for managing billing and subscriptions"""
    
    def __init__(self):
        self.plans = self._load_plan_configs()
        self.usage_cache = {}  # In-memory cache for usage data
        
    def _load_plan_configs(self) -> Dict[str, PlanConfig]:
        """Load billing plan configurations"""
        plans = {}
        
        # Free Plan
        plans["free"] = PlanConfig(
            plan_id="free",
            name="Free",
            description="Perfect for small teams getting started",
            price_monthly=Decimal("0"),
            price_yearly=Decimal("0"),
            max_users=5,
            max_projects=3,
            max_workflows=10,
            max_api_calls=1000,
            max_storage_gb=5,
            max_ai_tokens=10000,
            features=[
                "Basic multi-agent orchestration",
                "3 active projects",
                "Community support",
                "Basic reporting"
            ]
        )
        
        # Professional Plan
        plans["professional"] = PlanConfig(
            plan_id="professional",
            name="Professional",
            description="For growing teams that need more power",
            price_monthly=Decimal("299"),
            price_yearly=Decimal("2990"),
            max_users=50,
            max_projects=20,
            max_workflows=100,
            max_api_calls=10000,
            max_storage_gb=100,
            max_ai_tokens=100000,
            features=[
                "Advanced multi-agent orchestration",
                "20 active projects",
                "Priority support",
                "Advanced analytics",
                "Custom workflows",
                "API access",
                "Team collaboration",
                "SLA guarantees"
            ],
            stripe_product_id="prod_professional",
            stripe_price_monthly_id="price_professional_monthly",
            stripe_price_yearly_id="price_professional_yearly"
        )
        
        # Enterprise Plan
        plans["enterprise"] = PlanConfig(
            plan_id="enterprise",
            name="Enterprise",
            description="For large organizations with custom needs",
            price_monthly=Decimal("999"),
            price_yearly=Decimal("9990"),
            max_users=500,
            max_projects=100,
            max_workflows=1000,
            max_api_calls=100000,
            max_storage_gb=1000,
            max_ai_tokens=1000000,
            features=[
                "Unlimited multi-agent orchestration",
                "Unlimited projects",
                "24/7 dedicated support",
                "Custom integrations",
                "Advanced security",
                "Compliance certifications",
                "Custom AI models",
                "On-premise deployment option",
                "SLA 99.9% uptime"
            ],
            stripe_product_id="prod_enterprise",
            stripe_price_monthly_id="price_enterprise_monthly",
            stripe_price_yearly_id="price_enterprise_yearly"
        )
        
        return plans
    
    async def create_subscription(
        self,
        tenant_id: str,
        plan_id: str,
        billing_period: BillingPeriod,
        stripe_customer_id: Optional[str] = None,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new subscription for a tenant"""
        
        plan = self.plans.get(plan_id)
        if not plan:
            raise ValueError(f"Invalid plan ID: {plan_id}")
        
        # Free plan doesn't need Stripe
        if plan_id == "free":
            return {
                "subscription_id": f"sub_free_{tenant_id}",
                "plan_id": plan_id,
                "status": "active",
                "current_period_start": datetime.utcnow(),
                "current_period_end": datetime.utcnow() + timedelta(days=365),
                "stripe_subscription_id": None
            }
        
        # Create or retrieve Stripe customer
        if not stripe_customer_id:
            customer = stripe.Customer.create(
                metadata={"tenant_id": tenant_id}
            )
            stripe_customer_id = customer.id
        
        # Attach payment method if provided
        if payment_method_id:
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=stripe_customer_id
            )
            stripe.Customer.modify(
                stripe_customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
        
        # Get the appropriate price ID
        if billing_period == BillingPeriod.MONTHLY:
            price_id = plan.stripe_price_monthly_id
        else:
            price_id = plan.stripe_price_yearly_id
        
        # Create Stripe subscription
        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{"price": price_id}],
            metadata={
                "tenant_id": tenant_id,
                "plan_id": plan_id
            }
        )
        
        return {
            "subscription_id": subscription.id,
            "plan_id": plan_id,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
            "stripe_subscription_id": subscription.id,
            "stripe_customer_id": stripe_customer_id
        }
    
    async def update_subscription(
        self,
        subscription_id: str,
        new_plan_id: str,
        new_billing_period: Optional[BillingPeriod] = None
    ) -> Dict[str, Any]:
        """Update an existing subscription"""
        
        new_plan = self.plans.get(new_plan_id)
        if not new_plan:
            raise ValueError(f"Invalid plan ID: {new_plan_id}")
        
        # Handle downgrade to free
        if new_plan_id == "free":
            # Cancel Stripe subscription
            stripe.Subscription.delete(subscription_id)
            return {
                "subscription_id": subscription_id,
                "plan_id": new_plan_id,
                "status": "cancelled",
                "message": "Downgraded to free plan"
            }
        
        # Get new price ID
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        if new_billing_period:
            price_id = (new_plan.stripe_price_monthly_id 
                       if new_billing_period == BillingPeriod.MONTHLY 
                       else new_plan.stripe_price_yearly_id)
        else:
            # Keep current billing period
            current_price = subscription['items']['data'][0]['price']
            if 'monthly' in current_price['id']:
                price_id = new_plan.stripe_price_monthly_id
            else:
                price_id = new_plan.stripe_price_yearly_id
        
        # Update subscription
        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            items=[{
                'id': subscription['items']['data'][0].id,
                'price': price_id
            }],
            proration_behavior='create_prorations'
        )
        
        return {
            "subscription_id": updated_subscription.id,
            "plan_id": new_plan_id,
            "status": updated_subscription.status,
            "current_period_start": datetime.fromtimestamp(updated_subscription.current_period_start),
            "current_period_end": datetime.fromtimestamp(updated_subscription.current_period_end)
        }
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription"""
        
        # Cancel at period end to allow usage until paid period ends
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        
        return {
            "subscription_id": subscription.id,
            "status": "cancelled",
            "cancel_at": datetime.fromtimestamp(subscription.cancel_at) if subscription.cancel_at else None,
            "message": "Subscription will be cancelled at the end of the current billing period"
        }
    
    async def record_usage(
        self,
        tenant_id: str,
        metric: UsageMetric,
        quantity: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record usage for billing purposes"""
        
        record = UsageRecord(
            tenant_id=tenant_id,
            metric=metric,
            quantity=quantity,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store in cache (in production, use database)
        cache_key = f"{tenant_id}:{metric.value}:{record.timestamp.date()}"
        if cache_key not in self.usage_cache:
            self.usage_cache[cache_key] = []
        self.usage_cache[cache_key].append(record)
        
        logger.info(f"Recorded usage: {tenant_id} - {metric.value}: {quantity}")
    
    async def get_usage_summary(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage summary for a tenant"""
        
        summary = {
            "tenant_id": tenant_id,
            "period_start": start_date,
            "period_end": end_date,
            "metrics": {}
        }
        
        # Aggregate usage from cache
        for metric in UsageMetric:
            total = 0
            for date in self._daterange(start_date, end_date):
                cache_key = f"{tenant_id}:{metric.value}:{date}"
                if cache_key in self.usage_cache:
                    for record in self.usage_cache[cache_key]:
                        total += record.quantity
            
            summary["metrics"][metric.value] = total
        
        return summary
    
    async def calculate_usage_charges(
        self,
        tenant_id: str,
        plan_id: str,
        usage_summary: Dict[str, Any]
    ) -> Tuple[Decimal, List[Dict[str, Any]]]:
        """Calculate overage charges based on usage"""
        
        plan = self.plans.get(plan_id)
        if not plan:
            raise ValueError(f"Invalid plan ID: {plan_id}")
        
        total_charges = Decimal("0")
        line_items = []
        
        # API Calls overage
        api_calls = usage_summary["metrics"].get(UsageMetric.API_CALLS.value, 0)
        if api_calls > plan.max_api_calls:
            overage = api_calls - plan.max_api_calls
            charge = (Decimal(overage) / 1000) * plan.overage_api_calls_per_1000
            total_charges += charge
            line_items.append({
                "description": f"API Calls Overage ({overage:,} calls)",
                "quantity": overage,
                "unit_price": plan.overage_api_calls_per_1000,
                "amount": charge
            })
        
        # AI Tokens overage
        ai_tokens = usage_summary["metrics"].get(UsageMetric.AI_TOKENS.value, 0)
        if ai_tokens > plan.max_ai_tokens:
            overage = ai_tokens - plan.max_ai_tokens
            charge = (Decimal(overage) / 1000) * plan.overage_ai_tokens_per_1000
            total_charges += charge
            line_items.append({
                "description": f"AI Tokens Overage ({overage:,} tokens)",
                "quantity": overage,
                "unit_price": plan.overage_ai_tokens_per_1000,
                "amount": charge
            })
        
        # Storage overage
        storage_gb = usage_summary["metrics"].get(UsageMetric.STORAGE_GB.value, 0)
        if storage_gb > plan.max_storage_gb:
            overage = storage_gb - plan.max_storage_gb
            charge = Decimal(overage) * plan.overage_storage_per_gb
            total_charges += charge
            line_items.append({
                "description": f"Storage Overage ({overage} GB)",
                "quantity": overage,
                "unit_price": plan.overage_storage_per_gb,
                "amount": charge
            })
        
        return total_charges, line_items
    
    async def generate_invoice(
        self,
        tenant_id: str,
        subscription_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> Invoice:
        """Generate an invoice for a billing period"""
        
        # Get subscription details (mock for now)
        plan_id = "professional"  # Would get from subscription
        plan = self.plans[plan_id]
        
        # Get usage summary
        usage_summary = await self.get_usage_summary(tenant_id, period_start, period_end)
        
        # Calculate charges
        subscription_charge = plan.price_monthly  # Or yearly based on period
        usage_charges, usage_line_items = await self.calculate_usage_charges(
            tenant_id, plan_id, usage_summary
        )
        
        # Build line items
        line_items = [
            {
                "description": f"{plan.name} Plan Subscription",
                "quantity": 1,
                "unit_price": subscription_charge,
                "amount": subscription_charge
            }
        ]
        line_items.extend(usage_line_items)
        
        # Add per-agent breakdown (mock data)
        agent_usage = await self._get_agent_usage_breakdown(tenant_id, period_start, period_end)
        line_items.extend(agent_usage)
        
        # Create invoice
        invoice = Invoice(
            invoice_id=f"inv_{tenant_id}_{period_start.strftime('%Y%m')}",
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            subscription_charges=subscription_charge,
            usage_charges=usage_charges,
            total_amount=subscription_charge + usage_charges,
            line_items=line_items,
            status="draft",
            due_date=period_end + timedelta(days=30)
        )
        
        return invoice
    
    async def _get_agent_usage_breakdown(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> List[Dict[str, Any]]:
        """Get per-agent usage breakdown for invoice"""
        
        # Mock data - in production, aggregate from telemetry
        agent_breakdown = [
            {
                "description": "Ali Chief of Staff - 1,250 interactions",
                "quantity": 1250,
                "unit_price": Decimal("0.10"),
                "amount": Decimal("125.00"),
                "metadata": {"agent_id": "ali_chief_of_staff", "tokens": 45000}
            },
            {
                "description": "Amy CFO - 800 interactions",
                "quantity": 800,
                "unit_price": Decimal("0.08"),
                "amount": Decimal("64.00"),
                "metadata": {"agent_id": "amy_cfo", "tokens": 28000}
            },
            {
                "description": "Baccio Tech Architect - 650 interactions",
                "quantity": 650,
                "unit_price": Decimal("0.12"),
                "amount": Decimal("78.00"),
                "metadata": {"agent_id": "baccio_tech_architect", "tokens": 35000}
            }
        ]
        
        return agent_breakdown
    
    async def process_webhook(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Process Stripe webhook events"""
        
        logger.info(f"Processing webhook: {event_type}")
        
        if event_type == "invoice.payment_succeeded":
            # Mark invoice as paid
            invoice_id = event_data["id"]
            tenant_id = event_data["metadata"].get("tenant_id")
            logger.info(f"Payment successful for tenant {tenant_id}, invoice {invoice_id}")
            
        elif event_type == "invoice.payment_failed":
            # Handle failed payment
            invoice_id = event_data["id"]
            tenant_id = event_data["metadata"].get("tenant_id")
            logger.error(f"Payment failed for tenant {tenant_id}, invoice {invoice_id}")
            # Send notification, suspend services, etc.
            
        elif event_type == "customer.subscription.updated":
            # Handle subscription changes
            subscription_id = event_data["id"]
            logger.info(f"Subscription updated: {subscription_id}")
            
        elif event_type == "customer.subscription.deleted":
            # Handle cancellation
            subscription_id = event_data["id"]
            logger.info(f"Subscription cancelled: {subscription_id}")
    
    def _daterange(self, start_date: datetime, end_date: datetime):
        """Generate dates between start and end"""
        for n in range(int((end_date.date() - start_date.date()).days) + 1):
            yield start_date.date() + timedelta(n)
    
    async def get_billing_portal_url(self, stripe_customer_id: str) -> str:
        """Get Stripe billing portal URL for customer self-service"""
        
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url="https://convergio.ai/settings/billing"
        )
        
        return session.url
    
    async def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get current subscription status"""
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "plan_id": subscription.metadata.get("plan_id"),
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "trial_end": datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {e}")
            return {
                "subscription_id": subscription_id,
                "status": "error",
                "error": str(e)
            }


# Singleton instance
billing_service = BillingService()