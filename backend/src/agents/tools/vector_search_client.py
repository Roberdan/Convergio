"""
Vector Search Client Tool for Ali and Agent Ecosystem
Provides authenticated access to Convergio vector service for embeddings and search
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ..utils.config import get_settings

# Import generated protobuf
try:
    import grpc
    from proto import vector_pb2 as pb
    from proto import vector_pb2_grpc as pb_grpc
except ImportError:
    # Fallback for development
    grpc = None
    pb = None
    pb_grpc = None

class VectorSearchClient:
    """Client for making authenticated calls to Convergio vector service."""
    
    def __init__(self):
        self.settings = get_settings()
        self.vector_url = self.settings.vector_service_url
        self.channel = None
        self.stub = None
        self._service_secret = os.getenv("SERVICE_REGISTRY_SECRET")
        
        # In development, allow missing SERVICE_REGISTRY_SECRET
        if not self._service_secret:
            self._service_secret = "dev-secret"  # Fallback for development
    
    def connect(self) -> bool:
        """Connect to vector service with authentication."""
        if grpc is None:
            print("⚠️ gRPC not available, using mock responses")
            return False
            
        try:
            # Create metadata with service authentication
            metadata = grpc.Metadata()
            metadata.add('x-service-auth', self._service_secret)
            metadata.add('x-service-name', 'agents-service')
            
            # Create insecure channel (same as backend)
            self.channel = grpc.insecure_channel(self.vector_url)
            
            # Create stub with metadata
            self.stub = pb_grpc.VectorServiceStub(self.channel)
            
            return True
            
        except Exception as e:
            print(f"Failed to connect to vector service: {e}")
            return False
    
    def embed_text(self, text: str, metadata: dict = None) -> dict:
        """Embed text using vector service."""
        if grpc is None:
            # Mock response when gRPC is not available
            return {
                "vector": [0.1] * 1536,  # Mock embedding
                "dimensions": 1536,
                "model": "text-embedding-3-small",
                "embedding_time_ms": 50,
                "metadata": metadata or {}
            }
            
        if not self.stub:
            if not self.connect():
                return {"error": "Failed to connect to vector service"}
        
        try:
            # Create request
            request = pb.EmbedRequest(
                text=text,
                metadata=metadata or {}
            )
            
            # Make authenticated call
            metadata_grpc = grpc.Metadata()
            metadata_grpc.add('x-service-auth', self._service_secret)
            metadata_grpc.add('x-service-name', 'agents-service')
            
            response = self.stub.Embed(request, metadata=metadata_grpc)
            
            return {
                "vector": list(response.vector),
                "dimensions": response.dimensions,
                "model": response.model,
                "embedding_time_ms": response.embedding_time_ms,
                "metadata": dict(response.metadata)
            }
            
        except Exception as e:
            return {"error": f"Embedding failed: {e}"}
    
    def search_vectors(self, query_vector: list, limit: int = 10) -> dict:
        """Search vectors using vector service."""
        if not self.stub:
            if not self.connect():
                return {"error": "Failed to connect to vector service"}
        
        try:
            # Create request
            request = pb.SearchRequest(
                query_vector=query_vector,
                limit=limit
            )
            
            # Make authenticated call
            metadata_grpc = grpc.Metadata()
            metadata_grpc.add('x-service-auth', self._service_secret)
            metadata_grpc.add('x-service-name', 'agents-service')
            
            response = self.stub.Search(request, metadata=metadata_grpc)
            
            # Convert results
            results = []
            for result in response.results:
                results.append({
                    "id": result.id,
                    "vector": list(result.vector),
                    "similarity_score": result.similarity_score,
                    "text": result.text,
                    "metadata": dict(result.metadata)
                })
            
            return {
                "results": results,
                "search_time_ms": response.search_time_ms,
                "total_results": response.total_results,
                "index_name": response.index_name
            }
            
        except Exception as e:
            return {"error": f"Search failed: {e}"}
    
    def batch_embed(self, texts: list, metadata: dict = None) -> dict:
        """Batch embed texts using vector service."""
        if not self.stub:
            if not self.connect():
                return {"error": "Failed to connect to vector service"}
        
        try:
            # Create request
            request = pb.BatchEmbedRequest(
                texts=texts,
                metadata=metadata or {}
            )
            
            # Make authenticated call
            metadata_grpc = grpc.Metadata()
            metadata_grpc.add('x-service-auth', self._service_secret)
            metadata_grpc.add('x-service-name', 'agents-service')
            
            response = self.stub.BatchEmbed(request, metadata=metadata_grpc)
            
            # Convert embeddings
            embeddings = []
            for embedding in response.embeddings:
                embeddings.append({
                    "vector": list(embedding.vector),
                    "dimensions": embedding.dimensions,
                    "model": embedding.model,
                    "embedding_time_ms": embedding.embedding_time_ms,
                    "metadata": dict(embedding.metadata)
                })
            
            return {
                "embeddings": embeddings,
                "total_time_ms": response.total_time_ms,
                "batch_size": response.batch_size
            }
            
        except Exception as e:
            return {"error": f"Batch embedding failed: {e}"}
    
    def close(self):
        """Close the connection."""
        if self.channel:
            self.channel.close()

def get_vector_client() -> VectorSearchClient:
    """Get a vector search client instance, falling back gracefully in dev."""
    try:
        return VectorSearchClient()
    except Exception:
        # Fallback client shim when config/env isn't available
        class _DevClient:
            def embed_text(self, text: str, metadata: dict = None) -> dict:
                # Deterministic mock embedding based on text hash for stability
                import hashlib
                import random
                h = hashlib.sha256((text or "").encode()).hexdigest()
                rnd = random.Random(int(h[:8], 16))
                return {
                    "vector": [rnd.random() for _ in range(1536)],
                    "dimensions": 1536,
                    "model": "dev-mock-embedding",
                    "embedding_time_ms": 1,
                    "metadata": metadata or {}
                }

            def search_vectors(self, query_vector: list, limit: int = 10) -> dict:
                # Dev mock returns empty results
                return {"results": [], "total_results": 0, "search_time_ms": 1, "index_name": "dev-mock"}

            def close(self):
                return None

        return _DevClient()

async def embed_text(text: str) -> list:
    """Embed text and return the raw embedding vector (list[float]).

    This async wrapper provides a consistent contract for callers that `await` it.
    Returns an empty list on failure.
    """
    try:
        client = get_vector_client()
        result = client.embed_text(text)
        try:
            client.close()
        except Exception:
            pass

        if not isinstance(result, dict):
            return []
        if "error" in result:
            return []
        return result.get("vector", []) or []
    except Exception:
        return []

def calculate_similarity(vector1: list, vector2: list) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        vector1: First embedding vector
        vector2: Second embedding vector
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    import numpy as np
    
    # Convert to numpy arrays
    v1 = np.array(vector1)
    v2 = np.array(vector2)
    
    # Calculate cosine similarity
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    
    # Ensure result is between 0 and 1
    return max(0.0, min(1.0, similarity))


async def search_similar(query_vector: list, limit: int = 5) -> dict:
    """Search for similar vectors and return a structured result dict.

    Returns a dict with keys: results (list), total_results (int), search_time_ms (int), index_name (str).
    On error, includes an 'error' key and empty results.
    """
    try:
        client = get_vector_client()
        result = client.search_vectors(query_vector, limit)
        try:
            client.close()
        except Exception:
            pass

        if not isinstance(result, dict):
            return {"results": [], "total_results": 0, "search_time_ms": 0, "index_name": "unknown", "error": "Invalid response"}
        if "error" in result:
            # Normalize error shape
            return {
                "results": [],
                "total_results": 0,
                "search_time_ms": 0,
                "index_name": "unknown",
                "error": result.get("error")
            }
        # Ensure keys exist
        result.setdefault("results", [])
        result.setdefault("total_results", len(result.get("results", [])))
        result.setdefault("search_time_ms", 0)
        result.setdefault("index_name", "unknown")
        return result
    except Exception as e:
        return {"results": [], "total_results": 0, "search_time_ms": 0, "index_name": "unknown", "error": str(e)}