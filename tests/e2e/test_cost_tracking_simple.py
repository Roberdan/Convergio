#!/usr/bin/env python3
"""
💰 Simple Cost Tracking Test
Test the cost tracking system with real database
"""

import asyncio
import pytest
from decimal import Decimal
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "src"))

from src.core.database import get_async_session, init_db, close_db
from src.models.cost_tracking import CostTracking, CostSession
from sqlalchemy import select, func


class TestCostTrackingSimple:
    
    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """Initialize database before test class"""
        try:
            await init_db()
        except Exception:
            pass  # Already initialized
        yield
        # Database will be closed automatically
    
    @pytest.mark.asyncio
    async def test_cost_tracking_basic(self):
        """Test basic cost tracking operations"""
        
        async with get_async_session() as db:
            # Test 1: Create a cost tracking record
            cost_record = CostTracking(
                session_id="test_session_001",
                conversation_id="test_conv_001", 
                provider="openai",
                model="gpt-4o-mini",
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                input_cost_usd=Decimal("0.0001"),
                output_cost_usd=Decimal("0.0003"),
                total_cost_usd=Decimal("0.0004"),
                request_type="chat"
            )
            
            db.add(cost_record)
            await db.commit()
            await db.refresh(cost_record)
            
            # Test 2: Verify record was saved
            stmt = select(CostTracking).where(CostTracking.session_id == "test_session_001")
            result = await db.execute(stmt)
            saved_record = result.scalar_one_or_none()
            
            assert saved_record is not None
            assert saved_record.provider == "openai"
            assert saved_record.total_cost_usd == Decimal("0.0004")
            assert saved_record.total_tokens == 150
            
            # Test 3: Count all cost tracking records
            count_stmt = select(func.count(CostTracking.id))
            count_result = await db.execute(count_stmt)
            total_records = count_result.scalar()
            
            assert total_records > 0
            
            # Clean up test record
            await db.delete(saved_record)
            await db.commit()
            
            print(f"✅ Cost tracking test passed - {total_records} total records in database")

    @pytest.mark.asyncio 
    async def test_cost_session_basic(self):
        """Test cost session operations"""
        
        async with get_async_session() as db:
            # Test 1: Create a cost session
            session_record = CostSession(
                session_id="test_session_002",
                user_id="test_user",
                total_cost_usd=Decimal("0.0050"),
                total_tokens=500,
                total_interactions=5,
                provider_breakdown={"openai": {"cost": 0.005, "tokens": 500}},
                model_breakdown={"gpt-4o-mini": {"cost": 0.005, "tokens": 500}},
                agent_breakdown={}
            )
            
            db.add(session_record) 
            await db.commit()
            await db.refresh(session_record)
            
            # Test 2: Verify record was saved
            stmt = select(CostSession).where(CostSession.session_id == "test_session_002")
            result = await db.execute(stmt)
            saved_session = result.scalar_one_or_none()
            
            assert saved_session is not None
            assert saved_session.user_id == "test_user"
            assert saved_session.total_cost_usd == Decimal("0.0050")
            assert saved_session.total_tokens == 500
            
            # Test 3: Count all session records  
            count_stmt = select(func.count(CostSession.id))
            count_result = await db.execute(count_stmt)
            total_sessions = count_result.scalar()
            
            assert total_sessions > 0
            
            # Clean up test record
            await db.delete(saved_session)
            await db.commit()
            
            print(f"✅ Cost session test passed - {total_sessions} total sessions in database")

    @pytest.mark.asyncio
    async def test_real_cost_data(self):
        """Test with real cost tracking data from database"""
        
        async with get_async_session() as db:
            # Check existing cost tracking data
            cost_stmt = select(func.count(CostTracking.id))
            cost_result = await db.execute(cost_stmt)
            cost_count = cost_result.scalar()
            
            session_stmt = select(func.count(CostSession.id)) 
            session_result = await db.execute(session_stmt)
            session_count = session_result.scalar()
            
            # Get some sample data if it exists
            if cost_count > 0:
                sample_stmt = select(CostTracking).limit(3)
                sample_result = await db.execute(sample_stmt)
                sample_records = sample_result.scalars().all()
                
                for record in sample_records:
                    assert record.total_cost_usd >= 0
                    assert record.total_tokens >= 0
                    assert record.provider in ["openai", "anthropic", "perplexity", "google", "azure", "aws_bedrock", "custom"]
            
            print(f"✅ Real data test passed - {cost_count} cost records, {session_count} sessions")
            print(f"📊 Database has real cost tracking data: {'Yes' if cost_count > 0 else 'No'}")

if __name__ == "__main__":
    asyncio.run(TestCostTrackingSimple().test_cost_tracking_basic())
    asyncio.run(TestCostTrackingSimple().test_cost_session_basic()) 
    asyncio.run(TestCostTrackingSimple().test_real_cost_data())