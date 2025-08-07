#!/usr/bin/env python3
"""
Debug script to test agent response generation
"""

import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.core.config import settings
from src.agents.services.agent_loader import DynamicAgentLoader

async def debug_agent_response():
    print("🔍 Testing direct agent response...")
    
    # Load agent metadata
    loader = DynamicAgentLoader("src/agents/definitions")
    agent_metadata = loader.scan_and_load_agents()
    
    if "ali_chief_of_staff" not in agent_metadata:
        print("❌ Agent not found")
        return
    
    agent_meta = agent_metadata["ali_chief_of_staff"]
    print(f"✅ Found agent: {agent_meta.name}")
    
    # Create OpenAI client
    client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
    )
    
    # Create agent
    system_message = loader._build_system_message(agent_meta)
    agent = AssistantAgent(
        name="ali_chief_of_staff",
        model_client=client,
        system_message=system_message
    )
    
    print(f"✅ Created agent with system message length: {len(system_message)}")
    
    # Test message
    test_message = TextMessage(content="Come migliorare la produttività?", source="user")
    
    try:
        print("🔄 Running agent.run_stream()...")
        response_count = 0
        async for response in agent.run_stream(task=test_message):
            response_count += 1
            print(f"📥 Response {response_count}: {type(response)}")
            print(f"  hasattr messages: {hasattr(response, 'messages')}")
            
            if hasattr(response, 'messages'):
                print(f"  messages count: {len(response.messages) if response.messages else 0}")
                if response.messages:
                    for i, msg in enumerate(response.messages):
                        print(f"    Message {i}: {type(msg)}")
                        print(f"      hasattr content: {hasattr(msg, 'content')}")
                        print(f"      hasattr source: {hasattr(msg, 'source')}")
                        if hasattr(msg, 'content'):
                            content = msg.content
                            print(f"      content preview: {content[:100]}...")
                        if hasattr(msg, 'source'):
                            print(f"      source: {msg.source}")
                        
            if response_count >= 3:  # Limit to avoid infinite loop
                break
        
        print(f"✅ Agent response test completed - got {response_count} responses")
        
    except Exception as e:
        print(f"❌ Agent response test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_agent_response())