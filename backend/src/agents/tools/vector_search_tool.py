"""
Vector Search Tools for AutoGen Agents
Enables agents to perform semantic search on the vector database
"""

from typing import Any, Dict, List, Optional, Literal
import json
from datetime import datetime

import structlog
from pydantic import BaseModel
import httpx

# AutoGen imports with fallback
try:
    from autogen_core.tools import BaseTool
    AUTOGEN_CORE_AVAILABLE = True
except ImportError:
    BaseTool = object  # Use object as base class fallback
    AUTOGEN_CORE_AVAILABLE = False

logger = structlog.get_logger()


class VectorSearchArgs(BaseModel):
    """Arguments for vector search"""
    query: str
    top_k: int = 5
    search_type: Literal["semantic", "hybrid", "keyword"] = "semantic"
    filters: Optional[Dict[str, Any]] = None


class VectorSearchTool(BaseTool):
    """
    Tool for performing semantic vector search on the knowledge base.
    Connects to the internal vector search API.
    """

    def __init__(self, base_url: str = "http://localhost:9000"):
        if AUTOGEN_CORE_AVAILABLE:
            super().__init__(
                args_type=VectorSearchArgs,
                return_type=str,
                name="vector_search",
                description="Perform semantic search on the knowledge base using vector embeddings"
            )
        else:
            # Fallback for when autogen_core is not available
            self.args_type = VectorSearchArgs
            self.return_type = str
            self.name = "vector_search"
            self.description = "Perform semantic search on the knowledge base using vector embeddings"
        self.base_url = base_url
    
    async def run(self, args: VectorSearchArgs, cancellation_token=None) -> str:
        """
        Perform vector search.
        
        Args:
            args: Search arguments
            cancellation_token: Optional cancellation token for AutoGen
        
        Returns:
            JSON string with search results
        """
        try:
            logger.info(f"🔍 Vector search: {args.query}", top_k=args.top_k, search_type=args.search_type)
            
            # Call the vector search API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/vector/search",
                    json={
                        "query": args.query,
                        "top_k": args.top_k,
                        "search_type": args.search_type,
                        "filters": args.filters or {}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format results for clean markdown display
                    results = data.get("results", [])
                    if not results:
                        return f"🔍 **No results found** for query: '{args.query}'"
                    
                    markdown_results = [f"## 🔍 Search Results for: '{args.query}'\n"]
                    markdown_results.append(f"**Found {len(results)} relevant documents** ({args.search_type} search)\n")
                    
                    for i, result in enumerate(results[:5], 1):  # Limit to top 5 results
                        title = result.get("title", "Untitled")
                        content = result.get("content", "")
                        score = result.get("similarity_score", 0.0)
                        
                        # Truncate content for readability
                        content_preview = content[:300] + ("..." if len(content) > 300 else "")
                        
                        markdown_results.append(f"### {i}. {title}")
                        markdown_results.append(f"**Relevance Score:** {score:.2f}")
                        markdown_results.append(f"{content_preview}\n")
                    
                    return "\n".join(markdown_results)
                
                elif response.status_code == 404:
                    return "❌ **Vector search service not available** - the vector database is not running on port 9000."
                
                else:
                    return f"❌ **Vector search failed** with status {response.status_code}: {response.text}"
                    
        except httpx.ConnectError:
            logger.warning("Vector search service not available")
            return "❌ **Vector search service not available** - unable to connect to vector database on localhost:9000. Use database_query tool for document search instead."
            
        except Exception as e:
            logger.error(f"❌ Vector search error: {e}")
            return f"❌ **Vector Search Error**: {str(e)}"


class DocumentEmbeddingArgs(BaseModel):
    """Arguments for document embedding"""
    text: str
    document_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentEmbeddingTool(BaseTool):
    """
    Tool for creating embeddings for documents.
    Useful for indexing new content.
    """
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        if AUTOGEN_CORE_AVAILABLE:
            super().__init__(
                args_type=DocumentEmbeddingArgs,
                return_type=str,
                name="embed_document",
                description="Create vector embeddings for document text"
            )
        else:
            # Fallback for when autogen_core is not available
            self.args_type = DocumentEmbeddingArgs
            self.return_type = str
            self.name = "embed_document"
            self.description = "Create vector embeddings for document text"
        self.base_url = base_url
    
    async def run(self, args: DocumentEmbeddingArgs, cancellation_token=None) -> str:
        """
        Create document embedding.
        
        Args:
            args: Embedding arguments
            cancellation_token: Optional cancellation token for AutoGen
        
        Returns:
            JSON string with embedding result
        """
        try:
            logger.info("🔢 Creating embedding", text_length=len(args.text), doc_id=args.document_id)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/vector/embed",
                    json={
                        "text": args.text,
                        "document_id": args.document_id,
                        "metadata": args.metadata or {}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    result = {
                        "status": "success",
                        "embedding_id": data.get("embedding_id"),
                        "document_id": args.document_id,
                        "text_length": len(args.text),
                        "embedding_dimensions": len(data.get("embedding", [])),
                        "timestamp": datetime.now().isoformat(),
                    }
                    return json.dumps(result, indent=2)
                
                else:
                    err = {
                        "status": "error",
                        "error": f"Embedding failed with status {response.status_code}",
                        "message": response.text,
                    }
                    return json.dumps(err, indent=2)
                    
        except httpx.ConnectError:
            err = {
                "status": "error",
                "error": "Vector service not available",
                "message": "Unable to connect to vector database on localhost:9000",
            }
            return json.dumps(err, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Embedding error: {e}")
            err = {
                "status": "error",
                "error": str(e),
            }
            return json.dumps(err, indent=2)


# Export vector tools
VECTOR_TOOLS = [
    VectorSearchTool(),
    DocumentEmbeddingTool()
]


def get_vector_tools(base_url: str = "http://localhost:9000") -> List[BaseTool]:
    """
    Get all vector-related tools for AutoGen 0.7.2 agents.
    
    Args:
        base_url: Base URL for vector service
    
    Returns:
        List of properly configured vector tools for AutoGen
    """
    return [
        VectorSearchTool(base_url),
        DocumentEmbeddingTool(base_url)
    ]