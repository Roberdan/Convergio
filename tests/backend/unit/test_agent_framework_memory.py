"""
Unit tests for AgentFrameworkMemory (G4).
Tests memory storage, retrieval, and message format conversion.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch


class TestMemoryImports:
    """Tests for module imports."""

    def test_module_imports_successfully(self):
        """Test that memory module imports without error."""
        from src.agents.memory import agent_framework_memory
        assert agent_framework_memory is not None

    def test_framework_flags_exist(self):
        """Test that framework availability flags exist."""
        from src.agents.memory.agent_framework_memory import (
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE,
            REDIS_AVAILABLE,
            VECTOR_SEARCH_AVAILABLE
        )
        assert isinstance(AGENT_FRAMEWORK_AVAILABLE, bool)
        assert isinstance(AUTOGEN_AVAILABLE, bool)
        assert isinstance(REDIS_AVAILABLE, bool)
        assert isinstance(VECTOR_SEARCH_AVAILABLE, bool)

    def test_memory_class_exists(self):
        """Test that AgentFrameworkMemory class exists."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory
        assert AgentFrameworkMemory is not None


class TestMemoryMessage:
    """Tests for MemoryMessage dataclass."""

    def test_message_creation(self):
        """Test basic message creation."""
        from src.agents.memory.agent_framework_memory import MemoryMessage

        msg = MemoryMessage(
            id="test123",
            role="user",
            content="Hello",
            source="user"
        )

        assert msg.id == "test123"
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.source == "user"

    def test_message_default_timestamp(self):
        """Test that timestamp is set by default."""
        from src.agents.memory.agent_framework_memory import MemoryMessage

        msg = MemoryMessage(
            id="test",
            role="user",
            content="Test",
            source="user"
        )

        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, datetime)

    def test_message_to_dict(self):
        """Test message serialization."""
        from src.agents.memory.agent_framework_memory import MemoryMessage

        msg = MemoryMessage(
            id="test",
            role="assistant",
            content="Response",
            source="agent"
        )

        data = msg.to_dict()

        assert data["id"] == "test"
        assert data["role"] == "assistant"
        assert data["content"] == "Response"
        assert "timestamp" in data

    def test_message_from_dict(self):
        """Test message deserialization."""
        from src.agents.memory.agent_framework_memory import MemoryMessage

        data = {
            "id": "test123",
            "role": "user",
            "content": "Hello",
            "source": "user",
            "timestamp": "2025-01-01T12:00:00+00:00",
            "metadata": {"key": "value"}
        }

        msg = MemoryMessage.from_dict(data)

        assert msg.id == "test123"
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.metadata == {"key": "value"}


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_entry_creation(self):
        """Test memory entry creation."""
        from src.agents.memory.agent_framework_memory import MemoryEntry, MemoryType

        entry = MemoryEntry(
            id="entry1",
            memory_type=MemoryType.CONTEXT,
            content="Important context",
            agent_id="agent1",
            user_id="user1",
            conversation_id="conv1"
        )

        assert entry.id == "entry1"
        assert entry.memory_type == MemoryType.CONTEXT
        assert entry.content == "Important context"

    def test_entry_default_values(self):
        """Test default values are set."""
        from src.agents.memory.agent_framework_memory import MemoryEntry, MemoryType

        entry = MemoryEntry(
            id="test",
            memory_type=MemoryType.CONVERSATION,
            content="Test",
            agent_id="a",
            user_id="u",
            conversation_id="c"
        )

        assert entry.importance_score == 0.5
        assert entry.access_count == 0
        assert entry.created_at is not None
        assert entry.metadata == {}

    def test_entry_to_dict(self):
        """Test entry serialization."""
        from src.agents.memory.agent_framework_memory import MemoryEntry, MemoryType

        entry = MemoryEntry(
            id="test",
            memory_type=MemoryType.KNOWLEDGE,
            content="Knowledge",
            agent_id="a",
            user_id="u",
            conversation_id="c"
        )

        data = entry.to_dict()

        assert data["id"] == "test"
        assert data["memory_type"] == "knowledge"
        assert data["content"] == "Knowledge"


class TestConversationMemory:
    """Tests for ConversationMemory dataclass."""

    def test_conversation_creation(self):
        """Test conversation memory creation."""
        from src.agents.memory.agent_framework_memory import ConversationMemory

        conv = ConversationMemory(
            conversation_id="conv1",
            user_id="user1",
            agent_ids=["agent1"],
            messages=[]
        )

        assert conv.conversation_id == "conv1"
        assert conv.user_id == "user1"
        assert len(conv.messages) == 0

    def test_conversation_to_dict(self):
        """Test conversation serialization."""
        from src.agents.memory.agent_framework_memory import (
            ConversationMemory,
            MemoryMessage
        )

        msg = MemoryMessage(id="m1", role="user", content="Hi", source="user")
        conv = ConversationMemory(
            conversation_id="conv1",
            user_id="user1",
            agent_ids=["agent1"],
            messages=[msg]
        )

        data = conv.to_dict()

        assert data["conversation_id"] == "conv1"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Hi"

    def test_conversation_from_dict(self):
        """Test conversation deserialization."""
        from src.agents.memory.agent_framework_memory import ConversationMemory

        data = {
            "conversation_id": "conv1",
            "user_id": "user1",
            "agent_ids": ["agent1"],
            "messages": [
                {"id": "m1", "role": "user", "content": "Hi", "source": "user"}
            ],
            "context_summary": "Summary",
            "key_facts": ["fact1"],
            "topic_tags": ["topic1"],
            "created_at": "2025-01-01T12:00:00+00:00",
            "last_updated": "2025-01-01T12:00:00+00:00",
            "total_tokens": 100
        }

        conv = ConversationMemory.from_dict(data)

        assert conv.conversation_id == "conv1"
        assert len(conv.messages) == 1
        assert conv.context_summary == "Summary"


class TestAgentFrameworkMemoryInit:
    """Tests for AgentFrameworkMemory initialization."""

    def test_memory_initializes_without_redis(self):
        """Test memory initializes without Redis."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory

        memory = AgentFrameworkMemory()

        assert memory is not None
        assert memory.use_redis is False

    def test_memory_has_configuration(self):
        """Test memory has configuration values."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory

        memory = AgentFrameworkMemory()

        assert memory.memory_retention_days == 30
        assert memory.max_conversation_length == 100
        assert memory.similarity_threshold == 0.8


class TestMessageStorage:
    """Tests for message storage."""

    @pytest.mark.asyncio
    async def test_store_message(self):
        """Test storing a message."""
        from src.agents.memory.agent_framework_memory import (
            AgentFrameworkMemory,
            MemoryMessage
        )

        memory = AgentFrameworkMemory()

        msg = MemoryMessage(
            id="msg1",
            role="user",
            content="Hello",
            source="user"
        )

        msg_id = await memory.store_message(
            conversation_id="conv1",
            message=msg,
            agent_id="agent1",
            user_id="user1"
        )

        assert msg_id == "msg1"

    @pytest.mark.asyncio
    async def test_store_multiple_messages(self):
        """Test storing multiple messages."""
        from src.agents.memory.agent_framework_memory import (
            AgentFrameworkMemory,
            MemoryMessage
        )

        memory = AgentFrameworkMemory()

        for i in range(5):
            msg = MemoryMessage(
                id=f"msg{i}",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                source="user" if i % 2 == 0 else "agent1"
            )
            await memory.store_message(
                conversation_id="conv1",
                message=msg,
                agent_id="agent1",
                user_id="user1"
            )

        conv = await memory.get_conversation("conv1")
        assert len(conv.messages) == 5


class TestConversationRetrieval:
    """Tests for conversation retrieval."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self):
        """Test getting a conversation that doesn't exist."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory

        memory = AgentFrameworkMemory()

        conv = await memory.get_conversation("nonexistent")

        assert conv is None

    @pytest.mark.asyncio
    async def test_get_conversation_history(self):
        """Test getting conversation history with limit."""
        from src.agents.memory.agent_framework_memory import (
            AgentFrameworkMemory,
            MemoryMessage
        )

        memory = AgentFrameworkMemory()

        # Store 10 messages
        for i in range(10):
            msg = MemoryMessage(
                id=f"msg{i}",
                role="user",
                content=f"Message {i}",
                source="user"
            )
            await memory.store_message(
                conversation_id="conv1",
                message=msg,
                agent_id="agent1",
                user_id="user1"
            )

        # Get last 5
        history = await memory.get_conversation_history("conv1", limit=5)

        assert len(history) == 5
        assert history[-1].content == "Message 9"

    @pytest.mark.asyncio
    async def test_get_history_empty_conversation(self):
        """Test getting history for nonexistent conversation."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory

        memory = AgentFrameworkMemory()

        history = await memory.get_conversation_history("nonexistent")

        assert history == []


class TestContextManagement:
    """Tests for context management."""

    @pytest.mark.asyncio
    async def test_add_context(self):
        """Test adding context."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory

        memory = AgentFrameworkMemory()

        entry_id = await memory.add_context(
            conversation_id="conv1",
            context="Important information",
            importance=0.9
        )

        assert entry_id is not None

    @pytest.mark.asyncio
    async def test_get_context(self):
        """Test getting context entries."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory

        memory = AgentFrameworkMemory()

        await memory.add_context("conv1", "Context 1", importance=0.5)
        await memory.add_context("conv1", "Context 2", importance=0.9)
        await memory.add_context("conv1", "Context 3", importance=0.7)

        context = await memory.get_context("conv1")

        # Should be sorted by importance
        assert len(context) == 3
        assert context[0].content == "Context 2"  # Highest importance

    @pytest.mark.asyncio
    async def test_get_context_with_limit(self):
        """Test getting context with limit."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory

        memory = AgentFrameworkMemory()

        for i in range(10):
            await memory.add_context("conv1", f"Context {i}", importance=i/10)

        context = await memory.get_context("conv1", limit=3)

        assert len(context) == 3


class TestConversationClearing:
    """Tests for conversation clearing."""

    @pytest.mark.asyncio
    async def test_clear_conversation(self):
        """Test clearing a conversation."""
        from src.agents.memory.agent_framework_memory import (
            AgentFrameworkMemory,
            MemoryMessage
        )

        memory = AgentFrameworkMemory()

        # Store message
        msg = MemoryMessage(id="m1", role="user", content="Hi", source="user")
        await memory.store_message("conv1", msg, "agent1", "user1")

        # Verify it exists
        conv = await memory.get_conversation("conv1")
        assert conv is not None

        # Clear it
        result = await memory.clear_conversation("conv1")
        assert result is True

        # Verify it's gone
        conv = await memory.get_conversation("conv1")
        assert conv is None

    @pytest.mark.asyncio
    async def test_clear_nonexistent_conversation(self):
        """Test clearing a nonexistent conversation."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory

        memory = AgentFrameworkMemory()

        result = await memory.clear_conversation("nonexistent")

        assert result is False


class TestMemoryStats:
    """Tests for memory statistics."""

    def test_get_stats(self):
        """Test getting memory stats."""
        from src.agents.memory.agent_framework_memory import AgentFrameworkMemory

        memory = AgentFrameworkMemory()

        stats = memory.get_stats()

        assert "conversations_in_memory" in stats
        assert "context_entries" in stats
        assert "redis_enabled" in stats
        assert "vector_search_enabled" in stats

    @pytest.mark.asyncio
    async def test_stats_update_after_storage(self):
        """Test that stats update after storage."""
        from src.agents.memory.agent_framework_memory import (
            AgentFrameworkMemory,
            MemoryMessage
        )

        memory = AgentFrameworkMemory()

        initial_stats = memory.get_stats()
        assert initial_stats["conversations_in_memory"] == 0

        msg = MemoryMessage(id="m1", role="user", content="Hi", source="user")
        await memory.store_message("conv1", msg, "agent1", "user1")

        updated_stats = memory.get_stats()
        assert updated_stats["conversations_in_memory"] == 1


class TestGlobalInstance:
    """Tests for global memory instance."""

    def test_get_memory_system(self):
        """Test getting global memory system."""
        from src.agents.memory.agent_framework_memory import get_memory_system

        memory = get_memory_system()

        assert memory is not None

    def test_get_memory_system_singleton(self):
        """Test that get_memory_system returns singleton."""
        from src.agents.memory.agent_framework_memory import get_memory_system

        mem1 = get_memory_system()
        mem2 = get_memory_system()

        assert mem1 is mem2


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_accessible(self):
        """Test that all exports are accessible."""
        from src.agents.memory.agent_framework_memory import (
            AgentFrameworkMemory,
            MemoryMessage,
            MemoryEntry,
            ConversationMemory,
            MemoryType,
            get_memory_system,
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE,
            REDIS_AVAILABLE,
            VECTOR_SEARCH_AVAILABLE
        )

        assert AgentFrameworkMemory is not None
        assert MemoryMessage is not None
        assert MemoryEntry is not None
        assert ConversationMemory is not None
        assert MemoryType is not None
        assert get_memory_system is not None
