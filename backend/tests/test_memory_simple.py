"""
Simple AutoGen Memory System Test
"""

import asyncio
import sys
sys.path.append('.')

from src.core.redis import init_redis, close_redis
from src.agents.memory.autogen_memory_system import AutoGenMemorySystem

async def test_memory_simple():
    """Simple test for AutoGen Memory System"""
    print("🧠 Testing AutoGen Memory System (Simple)...")
    
    try:
        # Initialize Redis
        print("📊 Initializing Redis...")
        await init_redis()
        
        # Initialize memory system
        memory = AutoGenMemorySystem()
        print("✅ Memory system initialized successfully")
        
        # Test user preferences - this should work without complex dependencies
        print("👤 Testing user preferences...")
        
        # Update preferences
        test_preferences = {
            'communication_style': 'executive',
            'detail_level': 'high',
            'preferred_language': 'english'
        }
        
        await memory.update_user_preferences(
            user_id='test_user_001',
            preferences=test_preferences
        )
        print("✅ User preferences updated successfully")
        
        # Retrieve preferences
        retrieved_prefs = await memory.get_user_preferences('test_user_001')
        print(f"✅ Retrieved {len(retrieved_prefs)} user preferences")
        
        # Test cleanup functionality
        print("🧹 Testing memory cleanup...")
        cleaned_count = await memory.cleanup_old_memories()
        print(f"✅ Cleaned up {cleaned_count} old memories")
        
        print("🎯 AutoGen Memory System: BASIC TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            await close_redis()
        except:
            pass

if __name__ == "__main__":
    result = asyncio.run(test_memory_simple())
    print(f"🏁 Memory System Test Result: {'PASSED' if result else 'FAILED'}")