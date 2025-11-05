"""
INTEGRATION TEST - Agent Framework with Convergio
Tests the complete stack: Loader + Orchestrator + Workflow
"""

import asyncio
import os
from agent_framework.openai import OpenAIChatClient

# Test imports
print("=" * 60)
print("Testing Microsoft Agent Framework Integration")
print("=" * 60)

# Test 1: Import all components
print("\n✅ Test 1: Importing components...")
try:
    from src.agents.services.agent_framework_loader import AgentFrameworkLoader
    from src.agents.orchestrators.agent_framework_orchestrator import AgentFrameworkOrchestrator
    from src.agents.tools.agent_framework_tools import get_all_agent_framework_tools
    print("✅ All components imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 2: Check Agent Framework availability
print("\n✅ Test 2: Checking Agent Framework...")
try:
    from agent_framework import ChatAgent, WorkflowBuilder, ai_function
    print("✅ Agent Framework is available")
except Exception as e:
    print(f"❌ Agent Framework not available: {e}")
    exit(1)

# Test 3: Create loader
print("\n✅ Test 3: Creating loader...")
try:
    loader = AgentFrameworkLoader(
        agents_directory="/home/user/Convergio/backend/agents/definitions"
    )
    print(f"✅ Loader created with {len(loader.agent_metadata)} agent definitions")
except Exception as e:
    print(f"❌ Loader creation failed: {e}")
    exit(1)

# Test 4: Load tools
print("\n✅ Test 4: Loading tools...")
try:
    tools = get_all_agent_framework_tools()
    print(f"✅ Loaded {len(tools)} tools")
    for tool in tools[:3]:
        print(f"   - {tool.__name__}")
except Exception as e:
    print(f"❌ Tool loading failed: {e}")
    exit(1)


async def main():
    """Run async tests"""

    # Test 5: Create chat client
    print("\n✅ Test 5: Creating chat client...")
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("⚠️  OPENAI_API_KEY not set - skipping agent creation tests")
        print("   Set with: export OPENAI_API_KEY='sk-...'")
        return

    try:
        chat_client = OpenAIChatClient(api_key=api_key)
        print("✅ Chat client created")
    except Exception as e:
        print(f"❌ Chat client creation failed: {e}")
        return

    # Test 6: Create agents
    print("\n✅ Test 6: Creating agents...")
    try:
        agents = loader.create_chat_agents(chat_client, tools)
        print(f"✅ Created {len(agents)} agents:")
        for name in list(agents.keys())[:5]:
            print(f"   - {name}")
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 7: Create orchestrator
    print("\n✅ Test 7: Creating orchestrator...")
    try:
        orchestrator = AgentFrameworkOrchestrator(name="test_orchestrator")
        print("✅ Orchestrator created")
    except Exception as e:
        print(f"❌ Orchestrator creation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 8: Initialize orchestrator
    print("\n✅ Test 8: Initializing orchestrator with agents...")
    try:
        success = await orchestrator.initialize(
            agents=agents,
            agent_metadata=loader.agent_metadata
        )
        if success:
            print("✅ Orchestrator initialized successfully")
        else:
            print("❌ Orchestrator initialization returned False")
            return
    except Exception as e:
        print(f"❌ Orchestrator initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 9: Test simple orchestration
    print("\n✅ Test 9: Testing simple orchestration...")
    try:
        result = await orchestrator.orchestrate(
            message="Hello! What can you help me with?",
            context={"test_mode": True}
        )

        print("✅ Orchestration completed!")
        print(f"   Response: {result.get('response', 'No response')[:100]}...")
        print(f"   Duration: {result.get('duration_seconds', 0):.2f}s")
        print(f"   Workflow state: {result.get('workflow_state', 'unknown')}")

    except Exception as e:
        print(f"❌ Orchestration failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
