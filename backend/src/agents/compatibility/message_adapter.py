"""
Message Adapter - Converts between AutoGen and Agent Framework message formats
"""

from typing import Any, Dict, List, Union
import structlog

logger = structlog.get_logger()


class MessageAdapter:
    """
    Adapter to convert between AutoGen message format and Agent Framework
    message format during migration.
    """

    @staticmethod
    def autogen_to_agent_framework(autogen_message: Any) -> Any:
        """
        Convert AutoGen message to Agent Framework format.

        Args:
            autogen_message: AutoGen TextMessage or similar

        Returns:
            Agent Framework ChatMessage
        """
        try:
            from agent_framework.messages import ChatMessage

            # Extract content and source from AutoGen message
            content = getattr(autogen_message, "content", "")
            source = getattr(autogen_message, "source", "user")

            # Map source to role
            role_mapping = {
                "user": "user",
                "assistant": "assistant",
                "system": "system",
            }

            role = role_mapping.get(source.lower(), "user")

            return ChatMessage(role=role, content=content)

        except ImportError:
            logger.error("Agent Framework not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to convert message: {e}")
            raise

    @staticmethod
    def agent_framework_to_autogen(af_message: Any) -> Any:
        """
        Convert Agent Framework message to AutoGen format.

        Args:
            af_message: Agent Framework ChatMessage

        Returns:
            AutoGen TextMessage
        """
        try:
            from autogen_agentchat.messages import TextMessage

            # Extract content and role from AF message
            content = getattr(af_message, "content", "")
            role = getattr(af_message, "role", "user")

            # Map role to source
            source_mapping = {
                "user": "user",
                "assistant": "assistant",
                "system": "system",
            }

            source = source_mapping.get(role.lower(), "user")

            return TextMessage(content=content, source=source)

        except ImportError:
            logger.error("AutoGen not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to convert message: {e}")
            raise

    @staticmethod
    def extract_content(message: Any) -> str:
        """
        Extract content from message regardless of framework.

        Args:
            message: Message from either framework

        Returns:
            Message content as string
        """
        if hasattr(message, "content"):
            return str(message.content)
        return str(message)

    @staticmethod
    def convert_messages_list(
        messages: List[Any], target_framework: str = "agent_framework"
    ) -> List[Any]:
        """
        Convert a list of messages to target framework format.

        Args:
            messages: List of messages to convert
            target_framework: "autogen" or "agent_framework"

        Returns:
            List of converted messages
        """
        converted = []

        for msg in messages:
            try:
                if target_framework == "agent_framework":
                    converted_msg = MessageAdapter.autogen_to_agent_framework(msg)
                elif target_framework == "autogen":
                    converted_msg = MessageAdapter.agent_framework_to_autogen(msg)
                else:
                    raise ValueError(f"Unknown framework: {target_framework}")

                converted.append(converted_msg)

            except Exception as e:
                logger.warning(f"Failed to convert message, keeping original: {e}")
                converted.append(msg)

        return converted

    @staticmethod
    def to_dict(message: Any) -> Dict[str, Any]:
        """
        Convert message to dictionary format (framework-agnostic).

        Args:
            message: Message from either framework

        Returns:
            Dictionary representation
        """
        result = {}

        # Try to extract common fields
        if hasattr(message, "content"):
            result["content"] = message.content

        if hasattr(message, "role"):
            result["role"] = message.role
        elif hasattr(message, "source"):
            result["source"] = message.source

        if hasattr(message, "timestamp"):
            result["timestamp"] = str(message.timestamp)

        return result
