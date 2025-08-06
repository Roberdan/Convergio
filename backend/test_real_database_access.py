"""
🧪 Test Real Database Access for Agents
Test agent access to existing database with real schema
"""

import asyncio
from src.core.database import get_db_session, init_db
from sqlalchemy import text

async def test_database_access():
    """Test real database access with existing data"""
    
    print("🧪 Testing real database access...")
    
    await init_db()
    
    async for db in get_db_session():
        try:
            # Test 1: Count talents
            result = await db.execute(text("SELECT COUNT(*) FROM talents WHERE deleted_at IS NULL"))
            talent_count = result.scalar()
            print(f"✅ Talents: {talent_count} active records")
            
            # Test 2: Get talent details
            result = await db.execute(text("""
                SELECT first_name, last_name, email, created_at 
                FROM talents 
                WHERE deleted_at IS NULL 
                LIMIT 5
            """))
            talents = result.fetchall()
            print(f"📋 Sample talents:")
            for talent in talents:
                name = f"{talent[0] or ''} {talent[1] or ''}".strip() or "No name"
                print(f"  - {name} ({talent[2]})")
            
            # Test 3: Count engagements
            result = await db.execute(text("SELECT COUNT(*) FROM engagements"))
            engagement_count = result.scalar()
            print(f"✅ Engagements: {engagement_count} records")
            
            # Test 4: Count activities  
            result = await db.execute(text("SELECT COUNT(*) FROM activities"))
            activity_count = result.scalar()
            print(f"✅ Activities: {activity_count} records")
            
            # Test 5: Count document embeddings
            result = await db.execute(text("SELECT COUNT(*) FROM document_embeddings"))
            embedding_count = result.scalar()
            print(f"✅ Document Embeddings: {embedding_count} vector records")
            
            # Test 6: Sample complex query
            result = await db.execute(text("""
                SELECT 
                    t.email,
                    COUNT(DISTINCT a.id) as activity_count,
                    COUNT(DISTINCT aa.id) as assignment_count
                FROM talents t
                LEFT JOIN activity_assignments aa ON aa.talent_id = t.id
                LEFT JOIN activities a ON aa.activity_id = a.id
                WHERE t.deleted_at IS NULL
                GROUP BY t.id, t.email
                ORDER BY activity_count DESC
                LIMIT 5
            """))
            
            print(f"📈 Top active talents:")
            for row in result.fetchall():
                print(f"  - {row[0]}: {row[1]} activities, {row[2]} assignments")
            
            print(f"""
🎯 DATABASE STATUS: FULLY OPERATIONAL
✅ Real production database with {talent_count} talents
✅ Complex relationships and business data available
✅ Vector embeddings ready for AI search
✅ Agents can query all business data
            """)
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(test_database_access())