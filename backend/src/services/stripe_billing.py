"""
Stripe Billing Integration Service
Handles subscriptions, payments, and billing management
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import stripe
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.tenant import (
    Tenant, TenantStatus, SubscriptionPlan, BillingPeriod,
    Invoice, PaymentStatus
)

logger = structlog.get_logger()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


class StripeBillingService:
    """Service for managing Stripe billing operations"""
    
    def __init__(self):
        self.stripe = stripe
        self.webhook_secret = STRIPE_WEBHOOK_SECRET
        
        # Plan mapping
        self.plan_prices = {
            SubscriptionPlan.FREE: {
                "monthly": None,
                "yearly": None
            },
            SubscriptionPlan.STARTER: {
                "monthly": os.getenv("STRIPE_STARTER_MONTHLY_PRICE_ID"),
                "yearly": os.getenv("STRIPE_STARTER_YEARLY_PRICE_ID")
            },
            SubscriptionPlan.PROFESSIONAL: {
                "monthly": os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID"),
                "yearly": os.getenv("STRIPE_PRO_YEARLY_PRICE_ID")
            },
            SubscriptionPlan.ENTERPRISE: {
                "monthly": os.getenv("STRIPE_ENTERPRISE_MONTHLY_PRICE_ID"),
                "yearly": os.getenv("STRIPE_ENTERPRISE_YEARLY_PRICE_ID")
            }
        }
    
    async def create_customer(self, tenant: Tenant) -> str:
        """Create a Stripe customer for a tenant"""
        try:
            customer = self.stripe.Customer.create(
                email=tenant.email,
                name=tenant.name,
                metadata={
                    "tenant_id": str(tenant.id),
                    "tenant_slug": tenant.slug
                },
                description=f"Tenant: {tenant.name}"
            )
            
            logger.info("✅ Created Stripe customer", 
                       customer_id=customer.id,
                       tenant_id=tenant.id)
            
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to create Stripe customer: {e}")
            raise
    
    async def create_subscription(
        self,
        tenant: Tenant,
        plan: SubscriptionPlan,
        billing_period: BillingPeriod = BillingPeriod.MONTHLY,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a subscription for a tenant"""
        try:
            # Get price ID
            period = "monthly" if billing_period == BillingPeriod.MONTHLY else "yearly"
            price_id = self.plan_prices.get(plan, {}).get(period)
            
            if not price_id:
                raise ValueError(f"No price configured for {plan} {period}")
            
            # Ensure customer exists
            if not tenant.stripe_customer_id:
                tenant.stripe_customer_id = await self.create_customer(tenant)
            
            # Attach payment method if provided
            if payment_method_id:
                self.stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=tenant.stripe_customer_id
                )
                
                # Set as default payment method
                self.stripe.Customer.modify(
                    tenant.stripe_customer_id,
                    invoice_settings={
                        "default_payment_method": payment_method_id
                    }
                )
            
            # Create subscription
            subscription = self.stripe.Subscription.create(
                customer=tenant.stripe_customer_id,
                items=[{"price": price_id}],
                expand=["latest_invoice.payment_intent"],
                metadata={
                    "tenant_id": str(tenant.id),
                    "plan": plan,
                    "billing_period": billing_period
                },
                trial_period_days=14 if tenant.status == TenantStatus.TRIAL else 0
            )
            
            logger.info("✅ Created subscription",
                       subscription_id=subscription.id,
                       tenant_id=tenant.id,
                       plan=plan)
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "trial_end": datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice.payment_intent else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to create subscription: {e}")
            raise
    
    async def update_subscription(
        self,
        tenant: Tenant,
        new_plan: SubscriptionPlan,
        billing_period: Optional[BillingPeriod] = None
    ) -> Dict[str, Any]:
        """Update an existing subscription"""
        try:
            if not tenant.stripe_subscription_id:
                raise ValueError("No subscription found for tenant")
            
            # Get current subscription
            subscription = self.stripe.Subscription.retrieve(tenant.stripe_subscription_id)
            
            # Get new price ID
            period = "monthly" if (billing_period or tenant.billing_period) == BillingPeriod.MONTHLY else "yearly"
            new_price_id = self.plan_prices.get(new_plan, {}).get(period)
            
            if not new_price_id:
                raise ValueError(f"No price configured for {new_plan} {period}")
            
            # Update subscription
            updated = self.stripe.Subscription.modify(
                tenant.stripe_subscription_id,
                items=[{
                    "id": subscription.items.data[0].id,
                    "price": new_price_id
                }],
                proration_behavior="create_prorations",
                metadata={
                    "tenant_id": str(tenant.id),
                    "plan": new_plan,
                    "billing_period": billing_period or tenant.billing_period
                }
            )
            
            logger.info("✅ Updated subscription",
                       subscription_id=updated.id,
                       tenant_id=tenant.id,
                       new_plan=new_plan)
            
            return {
                "subscription_id": updated.id,
                "status": updated.status,
                "current_period_end": datetime.fromtimestamp(updated.current_period_end)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to update subscription: {e}")
            raise
    
    async def cancel_subscription(
        self,
        tenant: Tenant,
        at_period_end: bool = True
    ) -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            if not tenant.stripe_subscription_id:
                raise ValueError("No subscription found for tenant")
            
            if at_period_end:
                # Cancel at end of billing period
                subscription = self.stripe.Subscription.modify(
                    tenant.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # Cancel immediately
                subscription = self.stripe.Subscription.delete(
                    tenant.stripe_subscription_id
                )
            
            logger.info("✅ Cancelled subscription",
                       subscription_id=subscription.id,
                       tenant_id=tenant.id,
                       at_period_end=at_period_end)
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "cancel_at": datetime.fromtimestamp(subscription.cancel_at) if subscription.cancel_at else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to cancel subscription: {e}")
            raise
    
    async def create_payment_intent(
        self,
        tenant: Tenant,
        amount: int,  # in cents
        currency: str = "usd",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a one-time payment intent"""
        try:
            if not tenant.stripe_customer_id:
                tenant.stripe_customer_id = await self.create_customer(tenant)
            
            intent = self.stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=tenant.stripe_customer_id,
                description=description or f"Payment for {tenant.name}",
                metadata={
                    "tenant_id": str(tenant.id)
                }
            )
            
            logger.info("✅ Created payment intent",
                       intent_id=intent.id,
                       tenant_id=tenant.id,
                       amount=amount)
            
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount": amount,
                "currency": currency
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to create payment intent: {e}")
            raise
    
    async def create_usage_record(
        self,
        tenant: Tenant,
        quantity: int,
        timestamp: Optional[datetime] = None,
        action: str = "increment"
    ):
        """Report usage for metered billing"""
        try:
            if not tenant.stripe_subscription_id:
                raise ValueError("No subscription found for tenant")
            
            # Get subscription
            subscription = self.stripe.Subscription.retrieve(tenant.stripe_subscription_id)
            
            # Find metered item (if any)
            metered_item = None
            for item in subscription.items.data:
                if item.price.recurring.usage_type == "metered":
                    metered_item = item
                    break
            
            if not metered_item:
                return  # No metered billing for this subscription
            
            # Create usage record
            usage = self.stripe.SubscriptionItem.create_usage_record(
                metered_item.id,
                quantity=quantity,
                timestamp=int((timestamp or datetime.utcnow()).timestamp()),
                action=action  # "increment" or "set"
            )
            
            logger.info("✅ Created usage record",
                       subscription_id=tenant.stripe_subscription_id,
                       quantity=quantity)
            
            return usage
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to create usage record: {e}")
            raise
    
    async def create_checkout_session(
        self,
        tenant: Tenant,
        plan: SubscriptionPlan,
        billing_period: BillingPeriod,
        success_url: str,
        cancel_url: str
    ) -> str:
        """Create a Stripe Checkout session"""
        try:
            # Get price ID
            period = "monthly" if billing_period == BillingPeriod.MONTHLY else "yearly"
            price_id = self.plan_prices.get(plan, {}).get(period)
            
            if not price_id:
                raise ValueError(f"No price configured for {plan} {period}")
            
            # Ensure customer exists
            if not tenant.stripe_customer_id:
                tenant.stripe_customer_id = await self.create_customer(tenant)
            
            # Create checkout session
            session = self.stripe.checkout.Session.create(
                customer=tenant.stripe_customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "tenant_id": str(tenant.id),
                    "plan": plan,
                    "billing_period": billing_period
                }
            )
            
            logger.info("✅ Created checkout session",
                       session_id=session.id,
                       tenant_id=tenant.id)
            
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to create checkout session: {e}")
            raise
    
    async def create_billing_portal_session(
        self,
        tenant: Tenant,
        return_url: str
    ) -> str:
        """Create a billing portal session for customer self-service"""
        try:
            if not tenant.stripe_customer_id:
                raise ValueError("No Stripe customer found for tenant")
            
            session = self.stripe.billing_portal.Session.create(
                customer=tenant.stripe_customer_id,
                return_url=return_url
            )
            
            logger.info("✅ Created billing portal session",
                       tenant_id=tenant.id)
            
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to create billing portal session: {e}")
            raise
    
    async def handle_webhook(
        self,
        payload: bytes,
        signature: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            # Verify webhook signature
            event = self.stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            logger.info("📨 Received webhook event", type=event.type)
            
            # Handle different event types
            if event.type == "customer.subscription.created":
                await self._handle_subscription_created(event, db)
                
            elif event.type == "customer.subscription.updated":
                await self._handle_subscription_updated(event, db)
                
            elif event.type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event, db)
                
            elif event.type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(event, db)
                
            elif event.type == "invoice.payment_failed":
                await self._handle_payment_failed(event, db)
                
            elif event.type == "checkout.session.completed":
                await self._handle_checkout_completed(event, db)
            
            return {"status": "success", "event": event.type}
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"❌ Invalid webhook signature: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Webhook processing failed: {e}")
            raise
    
    async def _handle_subscription_created(self, event, db: AsyncSession):
        """Handle subscription creation"""
        subscription = event.data.object
        tenant_id = subscription.metadata.get("tenant_id")
        
        if tenant_id:
            # Update tenant
            tenant = await db.get(Tenant, tenant_id)
            if tenant:
                tenant.stripe_subscription_id = subscription.id
                tenant.status = TenantStatus.ACTIVE
                tenant.activated_at = datetime.utcnow()
                await db.commit()
                
                logger.info("✅ Updated tenant with subscription",
                          tenant_id=tenant_id,
                          subscription_id=subscription.id)
    
    async def _handle_subscription_updated(self, event, db: AsyncSession):
        """Handle subscription updates"""
        subscription = event.data.object
        tenant_id = subscription.metadata.get("tenant_id")
        
        if tenant_id:
            tenant = await db.get(Tenant, tenant_id)
            if tenant:
                # Update subscription details
                if subscription.status == "active":
                    tenant.status = TenantStatus.ACTIVE
                elif subscription.status == "canceled":
                    tenant.status = TenantStatus.CANCELLED
                elif subscription.status == "past_due":
                    tenant.status = TenantStatus.SUSPENDED
                
                await db.commit()
    
    async def _handle_subscription_deleted(self, event, db: AsyncSession):
        """Handle subscription deletion"""
        subscription = event.data.object
        tenant_id = subscription.metadata.get("tenant_id")
        
        if tenant_id:
            tenant = await db.get(Tenant, tenant_id)
            if tenant:
                tenant.status = TenantStatus.CANCELLED
                tenant.cancelled_at = datetime.utcnow()
                tenant.stripe_subscription_id = None
                await db.commit()
    
    async def _handle_payment_succeeded(self, event, db: AsyncSession):
        """Handle successful payment"""
        invoice = event.data.object
        tenant_id = invoice.metadata.get("tenant_id")
        
        if tenant_id:
            # Create invoice record
            invoice_record = Invoice(
                tenant_id=tenant_id,
                invoice_number=invoice.number,
                stripe_invoice_id=invoice.id,
                subtotal=Decimal(invoice.subtotal / 100),
                tax=Decimal(invoice.tax / 100) if invoice.tax else 0,
                total=Decimal(invoice.total / 100),
                currency=invoice.currency.upper(),
                status=PaymentStatus.SUCCEEDED,
                paid_at=datetime.fromtimestamp(invoice.status_transitions.paid_at),
                pdf_url=invoice.invoice_pdf
            )
            
            db.add(invoice_record)
            await db.commit()
            
            logger.info("✅ Payment succeeded",
                       tenant_id=tenant_id,
                       invoice_id=invoice.id)
    
    async def _handle_payment_failed(self, event, db: AsyncSession):
        """Handle failed payment"""
        invoice = event.data.object
        tenant_id = invoice.metadata.get("tenant_id")
        
        if tenant_id:
            tenant = await db.get(Tenant, tenant_id)
            if tenant:
                # Suspend tenant after multiple failures
                tenant.status = TenantStatus.SUSPENDED
                tenant.suspended_at = datetime.utcnow()
                await db.commit()
                
                logger.warning("⚠️ Payment failed, tenant suspended",
                             tenant_id=tenant_id)
    
    async def _handle_checkout_completed(self, event, db: AsyncSession):
        """Handle completed checkout"""
        session = event.data.object
        tenant_id = session.metadata.get("tenant_id")
        
        if tenant_id:
            tenant = await db.get(Tenant, tenant_id)
            if tenant:
                tenant.stripe_subscription_id = session.subscription
                tenant.status = TenantStatus.ACTIVE
                tenant.activated_at = datetime.utcnow()
                await db.commit()
                
                logger.info("✅ Checkout completed",
                          tenant_id=tenant_id,
                          subscription_id=session.subscription)


# Global service instance
stripe_billing = StripeBillingService()