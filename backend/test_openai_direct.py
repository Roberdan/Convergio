#!/usr/bin/env python3
"""
Test OpenAI API diretta per verificare funzionalità
"""

import sys
import asyncio
sys.path.insert(0, '/Users/roberdan/GitHub/convergio/backend')

from src.core.config import settings
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage

async def test_openai_direct():
    print("🔍 Testing direct OpenAI call...")
    
    try:
        # Create client
        client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
        )
        print("✅ Client created")
        
        # Create simple agent
        agent = AssistantAgent(
            name="test_agent",
            model_client=client,
            system_message="You are a helpful assistant. Respond in Italian."
        )
        print("✅ Agent created")
        
        # Test run (not run_stream first)
        print("🔄 Testing agent.run()...")
        response = await agent.run(task="Ciao, come stai?")
        print(f"✅ agent.run() response: {response}")
        
        # Test run_stream
        print("🔄 Testing agent.run_stream()...")
        message = TextMessage(content="Dimmi una barzelletta", source="user")
        
        response_count = 0
        async for response in agent.run_stream(task=message):
            response_count += 1
            print(f"📥 Stream response {response_count}: {type(response)}")
            
            if hasattr(response, 'messages') and response.messages:
                for msg in response.messages:
                    if hasattr(msg, 'content') and msg.content:
                        print(f"  Content: {msg.content[:100]}...")
                        return True  # Found content!
            
            if response_count >= 5:  # Limit
                break
        
        print(f"⚠️ Completed {response_count} responses, no content found")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_openai_direct())
    print(f"🎯 Direct OpenAI test: {'SUCCESS' if result else 'FAILED'}")