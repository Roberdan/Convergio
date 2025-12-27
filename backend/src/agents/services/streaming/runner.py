"""
True AutoGen Streaming Runner - Native streaming without simulation
Implements real AutoGen streaming with proper event handling and backpressure control.
NOTE: This module requires autogen_agentchat which is deprecated in favor of Agent Framework.
"""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, Set
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass
from enum import Enum

import structlog

# Conditional imports for autogen compatibility
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.messages import TextMessage, HandoffMessage, ToolCallRequestEvent, ToolCallExecutionEvent, ToolCallSummaryMessage
    AUTOGEN_AVAILABLE = True
except ImportError:
    # Fallback for Agent Framework migration
    AssistantAgent = None
    TextMessage = None
    HandoffMessage = None
    ToolCallRequestEvent = None
    ToolCallExecutionEvent = None
    ToolCallSummaryMessage = None
    AUTOGEN_AVAILABLE = False

from .response_types import StreamingResponse

logger = structlog.get_logger()


class StreamingEventType(Enum):
    """Native AutoGen streaming event types"""
    DELTA = "delta"
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    HANDOFF = "handoff"
    FINAL = "final"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    STATUS = "status"


@dataclass
class BackpressureConfig:
    """Configuration for backpressure management"""
    window_size: int = 10
    max_buffer_size: int = 50
    heartbeat_interval: float = 30.0
    chunk_delay: float = 0.0
    adaptive_delay: bool = True


class NativeAutoGenStreamer:
    """Native AutoGen streaming with proper event handling"""
    
    def __init__(self, backpressure_config: Optional[BackpressureConfig] = None):
        self.config = backpressure_config or BackpressureConfig()
        self.active_streams: Set[str] = set()
        self.stream_buffers: Dict[str, list] = {}
        
    async def stream_agent_response(
        self,
        agent: AssistantAgent,
        message: str,
        session,
        logger,
        enable_tools: bool = True,
        enable_handoffs: bool = True
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Stream agent response using native AutoGen streaming capabilities"""
        
        stream_id = str(uuid4())
        self.active_streams.add(stream_id)
        self.stream_buffers[stream_id] = []
        
        try:
            # Start heartbeat task
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(stream_id, session, logger)
            )
            
            logger.info(
                "🚀 Starting native AutoGen streaming",
                stream_id=stream_id,
                agent_name=session.agent_name,
                message_length=len(message)
            )
            
            # Track streaming state
            total_events = 0
            current_message = ""
            active_tools = {}
            
            # Main streaming loop using agent.run_stream() with correct AutoGen API
            # AutoGen's run_stream() expects a task string, not a TextMessage object
            async for response_chunk in agent.run_stream(task=message):
                total_events += 1
                
                # Apply backpressure control
                if await self._should_apply_backpressure(stream_id):
                    await self._apply_backpressure_delay(stream_id)
                
                # Handle AutoGen streaming response chunks
                # AutoGen streaming returns chunks that can contain:
                # - Partial text content
                # - Tool calls and results
                # - Status updates
                # - Final responses
                
                if hasattr(response_chunk, 'messages') and response_chunk.messages:
                    # Handle message-based responses
                    for msg in response_chunk.messages:
                        async for streaming_response in self._process_autogen_message(
                            msg, session, stream_id, active_tools, enable_tools, enable_handoffs
                        ):
                            if streaming_response.chunk_type == 'text':
                                current_message += streaming_response.content
                            yield streaming_response
                            
                elif hasattr(response_chunk, 'content'):
                    # Handle direct content streaming
                    if response_chunk.content:
                        yield StreamingResponse(
                            chunk_id=str(uuid4()),
                            session_id=session.session_id,
                            agent_name=session.agent_name,
                            chunk_type='text',
                            content=response_chunk.content,
                            timestamp=datetime.utcnow(),
                        )
                        current_message += response_chunk.content
                        
                elif isinstance(response_chunk, str):
                    # Handle string responses
                    yield StreamingResponse(
                        chunk_id=str(uuid4()),
                        session_id=session.session_id,
                        agent_name=session.agent_name,
                        chunk_type='text',
                        content=response_chunk,
                        timestamp=datetime.utcnow(),
                    )
                    current_message += response_chunk
                    
                else:
                    # Handle other response types
                    async for streaming_response in self._process_generic_response(
                        response_chunk, session, stream_id
                    ):
                        yield streaming_response
            
            # Send final completion event
            yield StreamingResponse(
                chunk_id=str(uuid4()),
                session_id=session.session_id,
                agent_name=session.agent_name,
                chunk_type='final',
                content=json.dumps({
                    "total_events": total_events,
                    "final_message": current_message,
                    "tools_used": list(active_tools.keys()),
                    "status": "completed"
                }),
                timestamp=datetime.utcnow(),
            )
            
            logger.info(
                "✅ Native AutoGen streaming completed",
                stream_id=stream_id,
                total_events=total_events,
                final_message_length=len(current_message)
            )
            
        except Exception as e:
            logger.error(
                "❌ Native AutoGen streaming error",
                stream_id=stream_id,
                error=str(e),
                agent_name=session.agent_name
            )
            
            # Send error response
            yield StreamingResponse(
                chunk_id=str(uuid4()),
                session_id=session.session_id,
                agent_name=session.agent_name,
                chunk_type='error',
                content=f"Native streaming error: {str(e)}",
                timestamp=datetime.utcnow()
            )
            
        finally:
            # Cleanup
            heartbeat_task.cancel()
            self.active_streams.discard(stream_id)
            self.stream_buffers.pop(stream_id, None)
    
    def _detect_event_type(self, event) -> StreamingEventType:
        """Detect the type of streaming event from AutoGen"""
        
        # Check for delta/incremental text
        if hasattr(event, 'delta') or (hasattr(event, 'choices') and event.choices):
            return StreamingEventType.DELTA
            
        # Check for tool calls
        if hasattr(event, 'tool_calls') or isinstance(event, (ToolCallRequestEvent, ToolCallSummaryMessage)):
            return StreamingEventType.TOOL_CALL
            
        # Check for tool results
        if hasattr(event, 'tool_results') or isinstance(event, ToolCallExecutionEvent):
            return StreamingEventType.TOOL_RESULT
            
        # Check for handoffs
        if isinstance(event, HandoffMessage) or hasattr(event, 'handoff_target'):
            return StreamingEventType.HANDOFF
            
        # Check for complete messages
        if hasattr(event, 'messages') and event.messages:
            return StreamingEventType.MESSAGE
            
        # Check for errors
        if hasattr(event, 'error') or hasattr(event, 'exception'):
            return StreamingEventType.ERROR
            
        # Default to delta for any content
        if hasattr(event, 'content'):
            return StreamingEventType.DELTA
            
        return StreamingEventType.STATUS
    
    async def _handle_delta_event(
        self, event, session, stream_id: str
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Handle streaming delta events"""
        
        content = ""
        
        # Extract content from different delta formats
        if hasattr(event, 'delta') and hasattr(event.delta, 'content'):
            content = event.delta.content
        elif hasattr(event, 'choices') and event.choices:
            choice = event.choices[0]
            if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                content = choice.delta.content
        elif hasattr(event, 'content'):
            content = event.content
        
        if content:
            yield StreamingResponse(
                chunk_id=str(uuid4()),
                session_id=session.session_id,
                agent_name=session.agent_name,
                chunk_type='text',
                content=content,
                timestamp=datetime.utcnow(),
            )
    
    async def _handle_tool_call_event(
        self, event, session, stream_id: str, active_tools: Dict[str, Any]
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Handle tool call events"""
        
        tool_calls = []
        
        # Extract tool calls from different formats
        if hasattr(event, 'tool_calls'):
            tool_calls = event.tool_calls
        elif isinstance(event, (ToolCallRequestEvent, ToolCallSummaryMessage)):
            tool_calls = [{"id": event.tool_call_id, "function": {"name": event.tool_name, "arguments": event.arguments}}]
        
        for tool_call in tool_calls:
            tool_id = tool_call.get('id', str(uuid4()))
            function_name = tool_call.get('function', {}).get('name', 'unknown_tool')
            arguments = tool_call.get('function', {}).get('arguments', {})
            
            # Track active tool
            active_tools[tool_id] = {
                "name": function_name,
                "arguments": arguments,
                "started_at": datetime.utcnow()
            }
            
            yield StreamingResponse(
                chunk_id=str(uuid4()),
                session_id=session.session_id,
                agent_name=session.agent_name,
                chunk_type='tool_call',
                content=json.dumps({
                    "tool_id": tool_id,
                    "tool_name": function_name,
                    "arguments": arguments
                }),
                timestamp=datetime.utcnow(),
            )
    
    async def _handle_tool_result_event(
        self, event, session, stream_id: str, active_tools: Dict[str, Any]
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Handle tool result events"""
        
        tool_results = []
        
        # Extract tool results from different formats
        if hasattr(event, 'tool_results'):
            tool_results = event.tool_results
        elif isinstance(event, ToolCallExecutionEvent):
            tool_results = [{"tool_call_id": event.tool_call_id, "content": event.content}]
        
        for tool_result in tool_results:
            tool_id = tool_result.get('tool_call_id', 'unknown')
            content = tool_result.get('content', str(tool_result))
            
            # Update active tool tracking
            if tool_id in active_tools:
                active_tools[tool_id]['completed_at'] = datetime.utcnow()
                active_tools[tool_id]['result'] = content
            
            yield StreamingResponse(
                chunk_id=str(uuid4()),
                session_id=session.session_id,
                agent_name=session.agent_name,
                chunk_type='tool_result',
                content=json.dumps({
                    "tool_id": tool_id,
                    "result": content,
                    "status": "completed"
                }),
                timestamp=datetime.utcnow(),
            )
    
    async def _handle_handoff_event(
        self, event, session, stream_id: str
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Handle handoff events"""
        
        target = "unknown"
        message = ""
        
        if isinstance(event, HandoffMessage):
            target = getattr(event, 'target', 'unknown')
            message = getattr(event, 'message', '')
        elif hasattr(event, 'handoff_target'):
            target = event.handoff_target
            message = getattr(event, 'message', '')
        
        yield StreamingResponse(
            chunk_id=str(uuid4()),
            session_id=session.session_id,
            agent_name=session.agent_name,
            chunk_type='handoff',
            content=json.dumps({
                "target_agent": target,
                "message": message,
                "handoff_type": "agent_transfer"
            }),
            timestamp=datetime.utcnow(),
        )
    
    async def _handle_message_event(
        self, event, session, stream_id: str
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Handle complete message events"""
        
        if hasattr(event, 'messages') and event.messages:
            for msg in event.messages:
                if hasattr(msg, 'content') and msg.content:
                    yield StreamingResponse(
                        chunk_id=str(uuid4()),
                        session_id=session.session_id,
                        agent_name=session.agent_name,
                        chunk_type='message',
                        content=msg.content,
                        timestamp=datetime.utcnow(),
                    )
    
    async def _handle_error_event(
        self, event, session, stream_id: str
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Handle error events"""
        
        error_msg = "Unknown streaming error"
        
        if hasattr(event, 'error'):
            error_msg = str(event.error)
        elif hasattr(event, 'exception'):
            error_msg = str(event.exception)
        
        yield StreamingResponse(
            chunk_id=str(uuid4()),
            session_id=session.session_id,
            agent_name=session.agent_name,
            chunk_type='error',
            content=error_msg,
            timestamp=datetime.utcnow(),
        )
    
    async def _process_autogen_message(
        self, 
        message, 
        session, 
        stream_id: str, 
        active_tools: Dict[str, Any],
        enable_tools: bool,
        enable_handoffs: bool
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Process AutoGen message objects according to their actual structure"""
        
        # Handle TextMessage
        if isinstance(message, TextMessage):
            if message.content:
                yield StreamingResponse(
                    chunk_id=str(uuid4()),
                    session_id=session.session_id,
                    agent_name=session.agent_name,
                    chunk_type='text',
                    content=message.content,
                    timestamp=datetime.utcnow(),
                )
        
        # Handle HandoffMessage
        elif isinstance(message, HandoffMessage):
            if enable_handoffs:
                target = getattr(message, 'target', 'unknown')
                handoff_message = getattr(message, 'message', '')
                yield StreamingResponse(
                    chunk_id=str(uuid4()),
                    session_id=session.session_id,
                    agent_name=session.agent_name,
                    chunk_type='handoff',
                    content=json.dumps({
                        "target_agent": target,
                        "message": handoff_message,
                        "handoff_type": "agent_transfer"
                    }),
                    timestamp=datetime.utcnow(),
                )
        
        # Handle ToolCallRequestEvent/ToolCallSummaryMessage
        elif isinstance(message, (ToolCallRequestEvent, ToolCallSummaryMessage)):
            if enable_tools:
                tool_name = getattr(message, 'tool_name', 'unknown_tool')
                arguments = getattr(message, 'arguments', {})
                tool_call_id = getattr(message, 'tool_call_id', str(uuid4()))
                
                # Track active tool
                active_tools[tool_call_id] = {
                    "name": tool_name,
                    "arguments": arguments,
                    "started_at": datetime.utcnow()
                }
                
                yield StreamingResponse(
                    chunk_id=str(uuid4()),
                    session_id=session.session_id,
                    agent_name=session.agent_name,
                    chunk_type='tool_call',
                    content=json.dumps({
                        "tool_id": tool_call_id,
                        "tool_name": tool_name,
                        "arguments": arguments
                    }),
                    timestamp=datetime.utcnow(),
                )
        
        # Handle ToolCallExecutionEvent
        elif isinstance(message, ToolCallExecutionEvent):
            if enable_tools:
                tool_call_id = getattr(message, 'tool_call_id', 'unknown')
                content = getattr(message, 'content', str(message))
                
                # Update active tool tracking
                if tool_call_id in active_tools:
                    active_tools[tool_call_id]['completed_at'] = datetime.utcnow()
                    active_tools[tool_call_id]['result'] = content
                
                yield StreamingResponse(
                    chunk_id=str(uuid4()),
                    session_id=session.session_id,
                    agent_name=session.agent_name,
                    chunk_type='tool_result',
                    content=json.dumps({
                        "tool_id": tool_call_id,
                        "result": content,
                        "status": "completed"
                    }),
                    timestamp=datetime.utcnow(),
                )
        
        # Handle generic message with content
        elif hasattr(message, 'content') and message.content:
            yield StreamingResponse(
                chunk_id=str(uuid4()),
                session_id=session.session_id,
                agent_name=session.agent_name,
                chunk_type='text',
                content=str(message.content),
                timestamp=datetime.utcnow(),
            )
    
    async def _process_generic_response(
        self, response_chunk, session, stream_id: str
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Process generic response chunks from AutoGen"""
        
        # Try to extract any useful content
        content = ""
        
        if hasattr(response_chunk, '__dict__'):
            # Try to find any text content in the response
            for attr_name in ['text', 'content', 'message', 'data']:
                if hasattr(response_chunk, attr_name):
                    attr_value = getattr(response_chunk, attr_name)
                    if attr_value and isinstance(attr_value, str):
                        content = attr_value
                        break
        
        if content:
            yield StreamingResponse(
                chunk_id=str(uuid4()),
                session_id=session.session_id,
                agent_name=session.agent_name,
                chunk_type='text',
                content=content,
                timestamp=datetime.utcnow(),
            )
        else:
            # Send status update for unrecognized chunks
            yield StreamingResponse(
                chunk_id=str(uuid4()),
                session_id=session.session_id,
                agent_name=session.agent_name,
                chunk_type='status',
                content=f"Processing: {type(response_chunk).__name__}",
                timestamp=datetime.utcnow(),
            )
    
    async def _should_apply_backpressure(self, stream_id: str) -> bool:
        """Check if backpressure should be applied"""
        buffer = self.stream_buffers.get(stream_id, [])
        return len(buffer) > self.config.window_size
    
    async def _apply_backpressure_delay(self, stream_id: str):
        """Apply intelligent backpressure delay"""
        buffer_size = len(self.stream_buffers.get(stream_id, []))
        
        if self.config.adaptive_delay:
            # Adaptive delay based on buffer size
            delay = min(0.1, buffer_size / self.config.max_buffer_size * 0.1)
        else:
            delay = self.config.chunk_delay
            
        if delay > 0:
            await asyncio.sleep(delay)
    
    async def _heartbeat_loop(self, stream_id: str, session, logger):
        """Send periodic heartbeat messages"""
        try:
            while stream_id in self.active_streams:
                await asyncio.sleep(self.config.heartbeat_interval)
                
                if stream_id in self.active_streams:
                    # Send heartbeat (would be handled by WebSocket layer)
                    logger.debug("💓 Streaming heartbeat", stream_id=stream_id)
                    
        except asyncio.CancelledError:
            logger.debug("🛑 Heartbeat cancelled", stream_id=stream_id)


# Global streamer instance
_native_streamer = NativeAutoGenStreamer()


# Legacy compatibility function
async def stream_agent_response(
    agent: AssistantAgent,
    message: str,
    session,
    logger,
) -> AsyncGenerator[StreamingResponse, None]:
    """Legacy compatibility wrapper using native AutoGen streaming"""
    
    async for response in _native_streamer.stream_agent_response(
        agent=agent,
        message=message,
        session=session,
        logger=logger
    ):
        yield response

