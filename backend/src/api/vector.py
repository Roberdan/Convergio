"""
🔍 Convergio - Vector Search API
Integrated vector embeddings and similarity search with pgvector
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import numpy as np

from ..core.database import get_db_session
from ..core.config import get_settings
from ..models.document import Document, DocumentEmbedding
from ..api.user_keys import get_user_api_key

logger = structlog.get_logger()
router = APIRouter(tags=["Vector Search"])

# Real OpenAI configuration
settings = get_settings()
OPENAI_API_URL = "https://vitaledopenaitest001.openai.azure.com/openai/v1/" #settings.OPENAI_API_BASE or os.getenv('OPENAI_APPI_BASE',"https://vitaledopenaitest001.openai.azure.com/openai/v1/")

def _openai_headers(request: Request) -> dict:
    """Build OpenAI headers using user session key if present, otherwise fallback to settings."""
    user_key = get_user_api_key(request, "openai") if request else None
    api_key = user_key or settings.OPENAI_API_KEY
    if not api_key:
        # Let downstream error produce a clear 401 from OpenAI
        api_key = ""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


# Request/Response models
class EmbeddingRequest(BaseModel):
    text: str
    model: str = "text-embedding-3-small"


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    model: str
    usage: Dict[str, int]


class DocumentIndexRequest(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    chunk_size: int = 1000
    chunk_overlap: int = 200


class DocumentIndexResponse(BaseModel):
    document_id: int
    chunks_created: int
    embeddings_generated: int
    status: str


class SimilaritySearchRequest(BaseModel):
    query: str
    top_k: int = 5
    similarity_threshold: float = 0.7
    filter_metadata: Optional[Dict[str, Any]] = None


class SimilaritySearchResult(BaseModel):
    document_id: int
    chunk_id: int
    title: str
    content: str
    similarity_score: float
    metadata: Optional[Dict[str, Any]]


class SimilaritySearchResponse(BaseModel):
    query: str
    results: List[SimilaritySearchResult]
    total_results: int
    processing_time_ms: int


@router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(
    request: EmbeddingRequest,
    http_request: Request,
):
    """
    🧠 Generate text embeddings
    
    Creates vector embeddings for the provided text using OpenAI
    """
    
    try:

        #https://vitaledopenaitest001.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-05-15

        # Generate embeddings using real OpenAI API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENAI_API_URL}/embeddings",
                headers=_openai_headers(http_request),
                json={
                    "input": request.text,
                    "model": request.model
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error("❌ OpenAI API error", 
                           status_code=response.status_code,
                           response=response.text)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="OpenAI API unavailable"
                )
            
            data = response.json()
            embedding = data['data'][0]['embedding']
            usage = data['usage']
        
        logger.info("✅ Real embeddings generated", 
                   model=request.model, 
                   tokens=usage['total_tokens'],
                   user_id=getattr(request, 'user_id', os.getenv("DEFAULT_ANONYMOUS_USER", "system_anonymous")))
        
        return EmbeddingResponse(
            embedding=embedding,
            model=request.model,
            usage=usage
        )
        
    except Exception as e:
        logger.error("❌ Embedding generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate embeddings"
        )


@router.post("/documents/index", response_model=DocumentIndexResponse)
async def index_document(
    request: DocumentIndexRequest,
    db: AsyncSession = Depends(get_db_session),
    http_request: Request = None,
):
    """
    📚 Index document with vector embeddings
    
    Splits document into chunks and generates embeddings for vector search
    """
    
    try:
        # Create document record
        document = await Document.create(
            db,
            title=request.title,
            content=request.content,
            doc_metadata=request.metadata or {},
        )
        
        # Split document into chunks
        chunks = _split_text(
            request.content, 
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        embeddings_created = 0
        
        # Generate embeddings for each chunk using real OpenAI
        for i, chunk in enumerate(chunks):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{OPENAI_API_URL}/embeddings",
                        headers=_openai_headers(http_request),
                        json={
                            "input": chunk,
                            "model": "text-embedding-ada-002"
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"OpenAI API error: {response.status_code}")
                    
                    data = response.json()
                    embedding = data['data'][0]['embedding']
                
                # Store embedding in database
                await DocumentEmbedding.create(
                    db,
                    document_id=document.id,
                    chunk_index=i,
                    chunk_text=chunk,
                    embedding=embedding,
                    embed_metadata={"chunk_size": len(chunk)}
                )
                
                embeddings_created += 1
                
            except Exception as e:
                logger.warning("⚠️ Failed to create embedding for chunk", 
                             chunk_index=i, error=str(e))
        
        logger.info("✅ Document indexed", 
                   document_id=document.id,
                   chunks=len(chunks),
                   embeddings=embeddings_created)
        
        return DocumentIndexResponse(
            document_id=document.id,
            chunks_created=len(chunks),
            embeddings_generated=embeddings_created,
            status="completed"
        )
        
    except Exception as e:
        logger.error("❌ Document indexing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to index document"
        )


@router.post("/search", response_model=SimilaritySearchResponse)
async def similarity_search(
    request: SimilaritySearchRequest,
    db: AsyncSession = Depends(get_db_session),
    http_request: Request = None,
):
    """
    🔍 Semantic similarity search
    
    Performs vector similarity search across indexed documents
    """
    
    start_time = datetime.utcnow()
    
    try:  
        # Generate query embedding using real OpenAI
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENAI_API_URL}/embeddings",
                headers=_openai_headers(http_request),
                json={
                    "input": request.query,
                    "model": "text-embedding-ada-002"
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code}")
            
            data = response.json()
            query_embedding = data['data'][0]['embedding']
        
        # Perform similarity search using pgvector
        from sqlalchemy import select, text
        import numpy as np
        
        # Convert query embedding to PostgreSQL vector format
        query_vector_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
        
        # Use pgvector's cosine similarity operator (<=>)
        # Lower score means higher similarity in cosine distance
        query = text("""
            SELECT 
                de.id,
                de.document_id,
                de.chunk_index,
                de.chunk_text,
                de.embed_metadata,
                d.title,
                1 - (de.embedding <=> cast(:query_vector as vector)) as similarity_score
            FROM document_embeddings de
            JOIN documents d ON de.document_id = d.id
            WHERE 1 - (de.embedding <=> cast(:query_vector as vector)) >= :threshold
            ORDER BY similarity_score DESC
            LIMIT :limit
        """)
        
        result = await db.execute(
            query,
            {"query_vector": query_vector_str, "threshold": request.similarity_threshold, "limit": request.top_k}
        )
        results = result.fetchall()
        
        # Format results
        search_results = []
        for row in results:
            search_results.append(SimilaritySearchResult(
                document_id=row.document_id,
                chunk_id=row.id,
                title=row.title,
                content=row.chunk_text,
                similarity_score=float(row.similarity_score),
                metadata=row.embed_metadata
            ))
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        logger.info("✅ Similarity search completed",
                   query=request.query[:50],
                   results_count=len(search_results),
                   processing_time_ms=processing_time)
        
        return SimilaritySearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error("❌ Similarity search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform similarity search"
        )


@router.get("/documents")
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📚 List indexed documents
    
    Returns paginated list of documents indexed by the user
    """
    
    try:
        documents = await Document.get_all(db, skip=skip, limit=limit)
        total_count = await Document.count_total(db)
        
        return {
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "content_length": len(doc.content),
                    "metadata": doc.doc_metadata,
                    "created_at": doc.created_at.isoformat(),
                    "embeddings_count": len(doc.embeddings) if doc.embeddings else 0
                }
                for doc in documents
            ],
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error("❌ Failed to list documents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📖 Get document details
    
    Returns document with its embeddings information
    """
    
    try:
        document = await Document.get_by_id(db, document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {
            "id": document.id,
            "title": document.title,
            "content": document.content,
        "metadata": document.doc_metadata,
            "created_at": document.created_at.isoformat(),
            "embeddings": [
                {
                    "id": emb.id,
                    "chunk_index": emb.chunk_index,
                    "chunk_text": emb.chunk_text[:200] + "..." if len(emb.chunk_text) > 200 else emb.chunk_text,
            "metadata": emb.embed_metadata
                }
                for emb in document.embeddings
            ] if document.embeddings else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get document", error=str(e), document_id=document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document"
        )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🗑️ Delete document and its embeddings
    
    Removes document and all associated vector embeddings
    """
    
    try:
        document = await Document.get_by_id(db, document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete document (embeddings will be cascade deleted)
        await document.delete(db)
        
        logger.info("✅ Document deleted", document_id=document_id, user_id=current_user.id)
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to delete document", error=str(e), document_id=document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.get("/stats")
async def get_vector_stats(
    db: AsyncSession = Depends(get_db_session)
):
    """
    📊 Get vector search statistics
    
    Returns statistics about indexed documents and embeddings
    """
    
    try:
        stats = await Document.get_stats(db)
        return stats
        
    except Exception as e:
        logger.error("❌ Failed to get vector stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vector statistics"
        )


# Helper functions
def _split_text(
    text: str, 
    chunk_size: int = 1000, 
    chunk_overlap: int = 200
) -> List[str]:
    """Split text into overlapping chunks"""
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Find the end of the chunk
        end = start + chunk_size
        
        if end >= len(text):
            # Last chunk
            chunks.append(text[start:])
            break
        
        # Try to break at a sentence or word boundary
        chunk = text[start:end]
        
        # Look for sentence boundaries
        last_sentence = max(
            chunk.rfind('. '),
            chunk.rfind('! '),
            chunk.rfind('? ')
        )
        
        if last_sentence > chunk_size * 0.5:  # At least 50% of chunk size
            end = start + last_sentence + 2
        else:
            # Look for word boundaries
            last_space = chunk.rfind(' ')
            if last_space > chunk_size * 0.5:
                end = start + last_space
        
        chunks.append(text[start:end])
        
        # Move start position with overlap
        start = end - chunk_overlap
        if start < 0:
            start = 0
    
    return chunks