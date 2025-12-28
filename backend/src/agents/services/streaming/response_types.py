"""
Streaming response data types extracted for file size hygiene.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class StreamingResponse:
    """Represents a streaming response chunk"""
    chunk_id: str
    session_id: str
    agent_name: str
    chunk_type: str  # 'text', 'thinking', 'complete', 'error', 'status', 'tool_call', 'tool_result', 'handoff'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


