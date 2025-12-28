"""
GroupChat Setup
Create SelectorGroupChat with settings-driven parameters.
"""

from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import List, Optional

from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
from .per_turn_rag import RAGEnhancedGroupChat, PerTurnRAGInjector
from src.agents.utils.config import get_settings
from .turn_by_turn_selector import TurnByTurnSelectorGroupChat
from .selection_policy import IntelligentSpeakerSelector as PolicySelector


def create_groupchat(
    participants: List[AssistantAgent],
    model_client: OpenAIChatCompletionClient,
    max_turns: int,
    rag_injector: Optional[PerTurnRAGInjector] = None,
    enable_per_turn_rag: bool = False,
    enable_turn_by_turn_selection: bool = False,
    intelligent_selector: Optional[PolicySelector] = None,
) -> SelectorGroupChat:
    """Create a GroupChat with optional per-turn RAG injection and intelligent selection"""
    settings = get_settings()
    max_turns = max_turns or getattr(settings, 'autogen_max_turns', 10)
    
    # Determine which GroupChat variant to use based on features
    if enable_turn_by_turn_selection:
        # Use turn-by-turn intelligent selection
        if enable_per_turn_rag and rag_injector:
            # Combine both features: create a class that has both
            class EnhancedGroupChat(TurnByTurnSelectorGroupChat, RAGEnhancedGroupChat):
                def __init__(self, **kwargs):
                    # Extract RAG-specific args
                    rag_injector = kwargs.pop('rag_injector', None)
                    # Initialize both parent classes
                    TurnByTurnSelectorGroupChat.__init__(self, **kwargs)
                    self.rag_injector = rag_injector
                    self.conversation_id = str(datetime.utcnow().timestamp()) if not hasattr(self, 'conversation_id') else self.conversation_id
                    self.user_id = "default" if not hasattr(self, 'user_id') else self.user_id
            
            return EnhancedGroupChat(
                participants=participants,
                model_client=model_client,
                allow_repeated_speaker=False,
                max_turns=max_turns,
                rag_injector=rag_injector,
                selector=intelligent_selector,
                enable_intelligent_selection=True
            )
        else:
            # Just turn-by-turn selection
            gc = TurnByTurnSelectorGroupChat(
                participants=participants,
                model_client=model_client,
                allow_repeated_speaker=False,
                max_turns=max_turns,
                selector=intelligent_selector,
                enable_intelligent_selection=True
            )
            # Attach timeout if the class supports it
            if hasattr(gc, 'timeout_seconds'):
                setattr(gc, 'timeout_seconds', getattr(settings, 'autogen_timeout_seconds', 120))
            return gc
    
    elif enable_per_turn_rag and rag_injector:
        # Just RAG enhancement
        gc = RAGEnhancedGroupChat(
            participants=participants,
            model_client=model_client,
            allow_repeated_speaker=False,
            max_turns=max_turns,
            rag_injector=rag_injector
        )
        if hasattr(gc, 'timeout_seconds'):
            setattr(gc, 'timeout_seconds', getattr(settings, 'autogen_timeout_seconds', 120))
        return gc
    else:
        # Standard SelectorGroupChat
        gc = SelectorGroupChat(
            participants=participants,
            model_client=model_client,
            allow_repeated_speaker=False,
            max_turns=max_turns,
        )
        if hasattr(gc, 'timeout_seconds'):
            setattr(gc, 'timeout_seconds', getattr(settings, 'autogen_timeout_seconds', 120))
        return gc


