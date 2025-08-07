#!/usr/bin/env python3
"""
Simple OpenAI test without complex imports
"""

import os
import asyncio

# Get API key from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

async def test_openai_simple():
    print("🔍 Simple OpenAI test...")
    print(f"API Key: {OPENAI_API_KEY[:20] if OPENAI_API_KEY else 'None'}...")
    
    if not OPENAI_API_KEY:
        print("❌ No API key found")
        return False
    
    try:
        # Direct OpenAI test with openai library
        import openai
        
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        print("🔄 Testing direct OpenAI call...")
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Respond in Italian briefly"},
                {"role": "user", "content": "Ciao, come stai?"}
            ],
            max_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"✅ OpenAI response: {content}")
        return True
        
    except ImportError:
        print("⚠️ openai library not available, trying AutoGen...")
        
        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            from autogen_agentchat.agents import AssistantAgent
            
            # Create client
            client = OpenAIChatCompletionClient(
                model="gpt-4o-mini",
                api_key=OPENAI_API_KEY,
            )
            
            # Create agent
            agent = AssistantAgent(
                name="test",
                model_client=client,
                system_message="Respond briefly in Italian."
            )
            
            print("🔄 Testing AutoGen agent.run()...")
            response = await agent.run(task="Come stai?")
            print(f"✅ AutoGen response: {response}")
            return True
            
        except Exception as e:
            print(f"❌ AutoGen test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_openai_simple())
    print(f"🎯 Test result: {'SUCCESS' if result else 'FAILED'}")