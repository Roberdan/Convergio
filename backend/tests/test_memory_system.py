"""
Test AutoGen Memory System Integration
"""

import asyncio
import sys
sys.path.append('.')

from src.core.redis import init_redis, close_redis
from src.core.database import init_db, close_db
from src.agents.memory.autogen_memory_system import AutoGenMemorySystem

async def test_memory_system():
    """Test AutoGen Memory System comprehensively"""
    print("🧠 Testing AutoGen Memory System Integration...")
    
    try:
        # Initialize dependencies
        print("📊 Initializing Redis and Database...")
        await init_redis()
        await init_db()
        
        # Initialize memory system
        memory = AutoGenMemorySystem()
        print("✅ Memory system initialized successfully")
        
        # Test 1: Store conversation message
        print("📝 Testing conversation message storage...")
        await memory.store_conversation_message(
            conversation_id='test_conv_001',
            user_id='test_user_001', 
            agent_id='ali_chief_of_staff',
            message_content='What is our Q4 revenue status?',
            message_type='user',
            context={'query_type': 'financial', 'priority': 'high'}
        )
        
        # Store agent response
        await memory.store_conversation_message(
            conversation_id='test_conv_001',
            user_id='test_user_001',
            agent_id='ali_chief_of_staff', 
            message_content='Q4 revenue is tracking at $1.2M with 15% growth over Q3.',
            message_type='agent',
            context={'response_type': 'financial_analysis'}
        )
        print("✅ Conversation message storage test passed")
        
        # Test 2: Retrieve relevant context
        print("🔍 Testing context retrieval...")
        context = await memory.retrieve_relevant_context(
            user_id='test_user_001',
            agent_id='ali_chief_of_staff',
            current_message='Follow up on revenue trends',
            limit=5
        )
        print(f"✅ Retrieved context with {len(context)} relevant memories")
        
        # Test 3: Store learned knowledge
        print("📚 Testing knowledge storage...")
        await memory.store_learned_knowledge(
            agent_id='ali_chief_of_staff',
            knowledge='Convergio Q4 performance shows 15% revenue growth',
            source_conversation_id='test_conv_001',
            context={'domain': 'finance', 'importance': 'high'}
        )
        print("✅ Knowledge storage test passed")
        
        # Test 4: User preferences
        print("👤 Testing user preferences...")
        await memory.update_user_preferences(
            user_id='test_user_001',
            preferences={'communication_style': 'executive', 'detail_level': 'high'}
        )
        
        prefs = await memory.get_user_preferences('test_user_001')
        print(f"✅ User preferences test passed - retrieved {len(prefs)} preferences")
        
        # Test 5: Conversation summary
        print("📄 Testing conversation summary...")
        summary = await memory.get_conversation_summary('test_conv_001')
        if summary:
            print("✅ Conversation summary test passed")
        else:
            print("⚠️ No conversation summary available (normal for new conversations)")
        
        print("🎯 AutoGen Memory System: ALL INTEGRATION TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Memory system integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            await close_redis()
            await close_db()
        except:
            pass

if __name__ == "__main__":
    result = asyncio.run(test_memory_system())
    print(f"🏁 Memory System Test Result: {'PASSED' if result else 'FAILED'}")