"""
Web Search Tool
Enables agents to search the internet for up-to-date information.
Supports both Agent Framework and AutoGen patterns.
"""

from typing import Any, Dict, List, Optional, Literal
import json
import asyncio
from datetime import datetime
import os

import structlog
from pydantic import BaseModel
import httpx

# Optional autogen import for backward compatibility
try:
    from autogen_core.tools import BaseTool
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    class BaseTool:
        """Placeholder BaseTool when AutoGen not installed."""
        def __init__(self, *args, **kwargs):
            pass

logger = structlog.get_logger()


class WebSearchArgs(BaseModel):
    """Arguments for web search"""
    query: str
    max_results: int = 5
    search_type: Literal["general", "news", "financial", "technical"] = "general"


class WebSearchTool(BaseTool):
    """
    Tool for searching the web for current information.
    Implements web search capabilities for AutoGen agents.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the web search tool.
        
        Args:
            api_key: API key for search service (Bing, Google, or Serper)
        """
        super().__init__(
            args_type=WebSearchArgs,
            return_type=str,
            name="web_search",
            description="Search the internet for current information, news, financial data, or technical documentation"
        )
        
        # Try to get API key from environment if not provided
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.search_provider = self._determine_provider()
    
    def _determine_provider(self) -> str:
        """Determine which search provider to use based on available API keys"""
        if os.getenv("PERPLEXITY_API_KEY"):
            return "perplexity"
        else:
            return "none"  # No provider configured

    def provider_health(self) -> Dict[str, Any]:
        """Return a lightweight health status for web search configuration.

        This does not make any network calls. It only reflects environment configuration.
        """
        provider = self._determine_provider()
        configured = provider == "perplexity"
        return {
            "provider": provider,
            "configured": configured,
            "note": "Using Perplexity for web search" if configured else "PERPLEXITY_API_KEY not configured"
        }
    
    async def run(self, args: WebSearchArgs, cancellation_token=None) -> str:
        """
        Perform a web search.
        
        Args:
            args: Search arguments containing query and options
            cancellation_token: Optional cancellation token for AutoGen
        
        Returns:
            Clean markdown formatted search results
        """
        try:
            logger.info(f"🔍 Web search: {args.query}", provider=self.search_provider)
            
            if self.search_provider == "perplexity":
                # Use Perplexity's Sonar model for web search via chat completions
                try:
                    api_key = os.getenv("PERPLEXITY_API_KEY")
                    if not api_key:
                        return "❌ **Web Search Error**: PERPLEXITY_API_KEY not configured in environment."
                    
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # Use sonar model which has internet access
                    payload = {
                        "model": "sonar",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful search assistant. Provide accurate, current information from the web."
                            },
                            {
                                "role": "user",
                                "content": f"Search the web for: {args.query}. Provide the top {args.max_results} most relevant results with titles, URLs, and brief descriptions."
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1000
                    }
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            "https://api.perplexity.ai/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=30.0
                        )
                        response.raise_for_status()
                        data = response.json()
                        
                        # Extract the response content
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        # Return clean markdown content
                        if content.strip():
                            return content.strip()
                        else:
                            return "❌ **No search results found** for your query."
                except Exception as e:
                    logger.error(f"Perplexity search failed: {e}")
                    return f"❌ **Web Search Error**: {str(e)}"
            else:
                # Fail loudly when no provider is configured
                return "❌ **Web Search Error**: No web search provider configured. Set PERPLEXITY_API_KEY in environment."
                
        except Exception as e:
            logger.error(f"❌ Web search error: {e}")
            return f"❌ **Web Search Failed**: {str(e)}"


class WebBrowseArgs(BaseModel):
    """Arguments for web browsing"""
    url: str
    action: Literal["read", "summarize", "extract"] = "read"
    selector: Optional[str] = None  # CSS selector for specific content


class WebBrowseTool(BaseTool):
    """
    Tool for browsing web pages and extracting content.
    Simpler alternative to full WebSurferAgent.
    """
    
    def __init__(self):
        super().__init__(
            args_type=WebBrowseArgs,
            return_type=str,
            name="web_browse",
            description="Browse a web page to read content, summarize, or extract specific information"
        )
    
    async def run(self, args: WebBrowseArgs, cancellation_token=None) -> str:
        """
        Browse a web page and extract content.
        
        Args:
            args: Browse arguments containing URL and action
            cancellation_token: Optional cancellation token for AutoGen
        
        Returns:
            Extracted content or summary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(args.url, follow_redirects=True)
                response.raise_for_status()
                
                # For now, return raw HTML preview
                # In production, you'd use BeautifulSoup or similar to parse
                content = response.text[:1000]  # First 1000 chars
                
                return f"""## 🌐 Web Page Content

**URL**: {args.url}
**Status**: {response.status_code}
**Action**: {args.action}

### Content Preview:
```
{content}
```

*Note: Full HTML parsing not implemented - use WebSurferAgent for advanced browsing*"""
                
        except Exception as e:
            logger.error(f"❌ Web browse error: {e}")
            return f"❌ **Web Browse Error**: {str(e)} (URL: {args.url})"


# Export all web tools
WEB_TOOLS = [
    WebSearchTool(),
    WebBrowseTool()
]


def get_web_tools(api_key: Optional[str] = None) -> List[BaseTool]:
    """
    Get all web-related tools for AutoGen agents.
    
    Args:
        api_key: Optional API key for search services
    
    Returns:
        List of web tools
    """
    return [
        WebSearchTool(api_key),
        WebBrowseTool()
    ]