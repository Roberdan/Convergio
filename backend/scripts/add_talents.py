#!/usr/bin/env python
"""
Add test talents to database
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import get_async_session, init_db
from src.models.talent import Talent


async def add_test_talents():
    """Add test talents to database"""
    
    # Initialize database
    await init_db()
    
    async with get_async_session() as session:
        try:
            # Create test talents (using only fields that exist in the model)
            talents = [
                Talent(
                    first_name="Alice",
                    last_name="Johnson",
                    email="alice@convergio.com"
                ),
                Talent(
                    first_name="Bob",
                    last_name="Smith",
                    email="bob@convergio.com"
                ),
                Talent(
                    first_name="Carol",
                    last_name="Davis",
                    email="carol@convergio.com"
                ),
                Talent(
                    first_name="David",
                    last_name="Wilson",
                    email="david@convergio.com"
                ),
                Talent(
                    first_name="Emma",
                    last_name="Martinez",
                    email="emma@convergio.com"
                ),
                Talent(
                    first_name="Frank",
                    last_name="Chen",
                    email="frank@convergio.com"
                ),
                Talent(
                    first_name="Grace",
                    last_name="Lee",
                    email="grace@convergio.com"
                ),
                Talent(
                    first_name="Henry",
                    last_name="Brown",
                    email="henry@convergio.com"
                ),
                Talent(
                    first_name="Isabella",
                    last_name="Garcia",
                    email="isabella@convergio.com"
                ),
                Talent(
                    first_name="James",
                    last_name="Anderson",
                    email="james@convergio.com"
                )
            ]
            
            # Check if talents already exist
            from sqlalchemy import select
            existing = await session.execute(select(Talent).limit(1))
            if existing.scalar():
                print("ℹ️ Talents already exist in database, skipping...")
                return
            
            # Add all talents
            for talent in talents:
                session.add(talent)
            
            # Commit all data
            await session.commit()
            
            print(f"✅ Successfully added {len(talents)} talents to database!")
            
            # Verify by counting
            result = await session.execute(select(Talent))
            all_talents = result.scalars().all()
            print(f"📊 Total talents in database: {len(all_talents)}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error adding talents: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(add_test_talents())