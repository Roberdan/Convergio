"""
Token Optimization Module
Implements AutoGen best practices for reducing token usage and costs
"""
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

class TokenOptimizer:
    """Optimizes token usage across agent conversations"""
    
    def __init__(self):
        self.response_cache: Dict[str, str] = {}
        self.cache_ttl = timedelta(minutes=15)
        self.cache_timestamps: Dict[str, datetime] = {}
    
    def get_cached_response(self, message: str, agent_id: str) -> Optional[str]:
        """Check if we have a cached response for this message"""
        cache_key = self._get_cache_key(message, agent_id)
        
        if cache_key in self.response_cache:
            # Check if cache is still valid
            if cache_key in self.cache_timestamps:
                if datetime.now() - self.cache_timestamps[cache_key] < self.cache_ttl:
                    logger.info("🎯 Cache hit", agent=agent_id, message_preview=message[:50])
                    return self.response_cache[cache_key]
        
        return None
    
    def cache_response(self, message: str, agent_id: str, response: str):
        """Cache a response for future use"""
        cache_key = self._get_cache_key(message, agent_id)
        self.response_cache[cache_key] = response
        self.cache_timestamps[cache_key] = datetime.now()
        
        # Clean old cache entries
        self._clean_cache()
    
    def _get_cache_key(self, message: str, agent_id: str) -> str:
        """Generate a cache key for message + agent combination"""
        content = f"{agent_id}:{message.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _clean_cache(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in self.cache_timestamps.items()
            if now - timestamp > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.response_cache[key]
            del self.cache_timestamps[key]
    
    @staticmethod
    def compress_message_history(messages: List[Dict], max_messages: int = 10) -> List[Dict]:
        """Compress message history to reduce context tokens"""
        if len(messages) <= max_messages:
            return messages
        
        # Keep first message (task) and last N-1 messages
        compressed = [messages[0]] + messages[-(max_messages-1):]
        
        # Add a summary message if we dropped messages
        dropped_count = len(messages) - max_messages
        if dropped_count > 0:
            summary = {
                "role": "system",
                "content": f"[{dropped_count} previous messages omitted for brevity]"
            }
            compressed.insert(1, summary)
        
        return compressed
    
    @staticmethod
    def truncate_response(response: str, max_length: int = 500) -> str:
        """Truncate long responses intelligently"""
        if len(response) <= max_length:
            return response
        
        # Try to truncate at sentence boundary
        truncated = response[:max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        
        cut_point = max(last_period, last_newline)
        if cut_point > max_length * 0.7:  # If we found a good cut point
            return truncated[:cut_point+1] + "..."
        
        return truncated + "..."
    
    @staticmethod
    def optimize_model_params(model_name: str = "") -> Dict[str, Any]:
        """Return optimized model parameters for token reduction
        
        Args:
            model_name: The model name to optimize for (e.g., 'gpt-4', 'gpt-3.5')
        """
        base_params = {
            "temperature": 0.3,  # Lower temperature for more focused responses
            "top_p": 0.9,       # Nucleus sampling for quality
            "frequency_penalty": 0.5,  # Reduce repetition
            "presence_penalty": 0.3,   # Encourage conciseness
            "max_tokens": 150,  # Limit response length for all models
        }
        
        return base_params
    
    @staticmethod
    def should_use_cheaper_model(message_type: str) -> bool:
        """Determine if we can use a cheaper model for this message type"""
        cheap_types = ["greeting", "simple_query", "status_check"]
        return message_type in cheap_types