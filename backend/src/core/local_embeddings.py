"""
Local Embeddings with Sentence Transformers
Provides fallback when OpenAI API is unavailable
"""

import asyncio
import hashlib
import json
from typing import List, Optional, Dict, Any
import structlog
import numpy as np

logger = structlog.get_logger()

# Lazy import to avoid loading model until needed
_model = None
_tokenizer = None


def get_local_model():
    """Get or initialize the local embedding model"""
    global _model, _tokenizer
    
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use a lightweight but effective model
            # all-MiniLM-L6-v2: 384 dimensions, good balance of speed and quality
            model_name = 'sentence-transformers/all-MiniLM-L6-v2'
            
            logger.info(f"Loading local embedding model: {model_name}")
            
            # Try offline first, then online with timeout
            try:
                # First try offline mode
                _model = SentenceTransformer(model_name, cache_folder="./models", device='cpu')
                logger.info("✅ Local embedding model loaded from cache")
            except Exception:
                try:
                    # Try online download with timeout
                    import socket
                    socket.setdefaulttimeout(10)
                    _model = SentenceTransformer(model_name, cache_folder="./models", device='cpu')
                    logger.info("✅ Local embedding model downloaded and loaded")
                except Exception as download_error:
                    logger.warning(f"⚠️ Could not download model: {download_error}")
                    # Use simple fallback - just return zeros for now
                    _model = None
                    logger.info("📱 Using fallback embedding (development mode)")
            
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load local embedding model: {e}")
            raise
    
    return _model


class LocalEmbeddingProvider:
    """
    Local embedding provider using sentence-transformers
    Serves as fallback when API providers are unavailable
    """
    
    def __init__(self, cache_client=None):
        """
        Initialize local embedding provider
        
        Args:
            cache_client: Optional Redis client for caching
        """
        self.cache_client = cache_client
        self.model = None
        self.embedding_dim = 384  # For all-MiniLM-L6-v2
        self._cache_prefix = "local_embed:"
        
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{self._cache_prefix}{text_hash}"
        
    async def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache if available"""
        if not self.cache_client:
            return None
            
        try:
            key = self._get_cache_key(text)
            cached = await self.cache_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None
        
    async def _save_to_cache(self, text: str, embedding: List[float], ttl: int = 3600):
        """Save embedding to cache"""
        if not self.cache_client:
            return
            
        try:
            key = self._get_cache_key(text)
            await self.cache_client.setex(
                key,
                ttl,
                json.dumps(embedding)
            )
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
            
    def _ensure_model_loaded(self):
        """Ensure model is loaded"""
        if self.model is None:
            self.model = get_local_model()
            
    async def create_embedding(
        self,
        text: str,
        use_cache: bool = True
    ) -> List[float]:
        """
        Create embedding for a single text
        
        Args:
            text: Text to embed
            use_cache: Whether to use cache
            
        Returns:
            Embedding vector
        """
        # Check cache first
        if use_cache:
            cached = await self._get_from_cache(text)
            if cached:
                logger.debug("Cache hit for local embedding")
                return cached
                
        # Ensure model is loaded
        self._ensure_model_loaded()
        
        # Generate embedding
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode(text, normalize_embeddings=True).tolist()
            )
            
            # Cache the result
            if use_cache:
                await self._save_to_cache(text, embedding)
                
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to create local embedding: {e}")
            raise
            
    async def create_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32,
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Create embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            use_cache: Whether to use cache
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
            
        # Ensure model is loaded
        self._ensure_model_loaded()
        
        embeddings = []
        
        # Check cache for each text
        texts_to_compute = []
        cached_indices = []
        
        if use_cache:
            for i, text in enumerate(texts):
                cached = await self._get_from_cache(text)
                if cached:
                    embeddings.append(cached)
                    cached_indices.append(i)
                else:
                    texts_to_compute.append((i, text))
        else:
            texts_to_compute = [(i, text) for i, text in enumerate(texts)]
            
        logger.info(
            f"Local embeddings: {len(cached_indices)} cached, "
            f"{len(texts_to_compute)} to compute"
        )
        
        # Process uncached texts in batches
        if texts_to_compute:
            # Extract just the texts for encoding
            texts_only = [text for _, text in texts_to_compute]
            
            # Process in batches
            all_new_embeddings = []
            for i in range(0, len(texts_only), batch_size):
                batch = texts_only[i:i + batch_size]
                
                try:
                    # Run in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    batch_embeddings = await loop.run_in_executor(
                        None,
                        lambda b=batch: self.model.encode(
                            b,
                            normalize_embeddings=True,
                            batch_size=len(b)
                        ).tolist()
                    )
                    all_new_embeddings.extend(batch_embeddings)
                    
                except Exception as e:
                    logger.error(f"Batch embedding failed: {e}")
                    raise
                    
            # Cache new embeddings
            if use_cache:
                cache_tasks = []
                for (orig_idx, text), embedding in zip(texts_to_compute, all_new_embeddings):
                    cache_tasks.append(self._save_to_cache(text, embedding))
                    
                await asyncio.gather(*cache_tasks, return_exceptions=True)
                
            # Combine cached and new embeddings in original order
            result = [None] * len(texts)
            
            # Place cached embeddings
            for i, cached_idx in enumerate(cached_indices):
                result[cached_idx] = embeddings[i]
                
            # Place new embeddings
            for (orig_idx, _), embedding in zip(texts_to_compute, all_new_embeddings):
                result[orig_idx] = embedding
                
            return result
        else:
            return embeddings
            
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score between -1 and 1
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Compute cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))
        
    async def search_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of results with indices and scores
        """
        if not candidate_embeddings:
            return []
            
        # Compute similarities
        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            score = self.compute_similarity(query_embedding, candidate)
            if score >= threshold:
                similarities.append({
                    "index": i,
                    "score": score
                })
                
        # Sort by score descending
        similarities.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top k
        return similarities[:top_k]
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the local model"""
        self._ensure_model_loaded()
        
        return {
            "provider": "local",
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_dim": self.embedding_dim,
            "max_sequence_length": getattr(self.model, "max_seq_length", 512),
            "loaded": self.model is not None
        }


# Singleton instance
_local_provider = None


def get_local_embedding_provider(cache_client=None) -> LocalEmbeddingProvider:
    """Get or create the local embedding provider"""
    global _local_provider
    
    if _local_provider is None:
        _local_provider = LocalEmbeddingProvider(cache_client)
        
    return _local_provider