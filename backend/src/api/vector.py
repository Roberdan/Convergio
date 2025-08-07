"""
🔍 Convergio - Vector Search API
Integrated vector embeddings and similarity search with pgvector
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import numpy as np

from src.core.database import get_db_session
from src.core.config import get_settings
from src.models.document import Document, DocumentEmbedding

logger = structlog.get_logger()
router = APIRouter(tags=["Vector Search"])

# Real OpenAI configuration
settings = get_settings()
OPENAI_API_URL = "https://api.openai.com/v1"
OPENAI_HEADERS = {
    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
    "Content-Type": "application/json"
}


# Request/Response models
class EmbeddingRequest(BaseModel):
    text: str
    model: str = "text-embedding-ada-002"


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
):
    """
    🧠 Generate text embeddings
    
    Creates vector embeddings for the provided text using OpenAI
    """
    
    try:
        # Generate embeddings using real OpenAI API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENAI_API_URL}/embeddings",
                headers=OPENAI_HEADERS,
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
                   user_id="anonymous")
        
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
    db: AsyncSession = Depends(get_db_session)
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
            metadata=request.metadata or {},
            user_id=current_user.id
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
                        headers=OPENAI_HEADERS,
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
                    metadata={"chunk_size": len(chunk)}
                )
                
                embeddings_created += 1
                
            except Exception as e:
                logger.warning("⚠️ Failed to create embedding for chunk", 
                             chunk_index=i, error=str(e))
        
        logger.info("✅ Document indexed", 
                   document_id=document.id,
                   chunks=len(chunks),
                   embeddings=embeddings_created,
                   user_id=current_user.id)
        
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
    db: AsyncSession = Depends(get_db_session)
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
                headers=OPENAI_HEADERS,
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
        
        # Perform similarity search
        results = await DocumentEmbedding.similarity_search(
            db,
            query_embedding=query_embedding,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            filter_metadata=request.filter_metadata
        )
        
        # Format results
        search_results = []
        for result in results:
            search_results.append(SimilaritySearchResult(
                document_id=result.document_id,
                chunk_id=result.id,
                title=result.document.title,
                content=result.chunk_text,
                similarity_score=result.similarity_score,
                metadata=result.metadata
            ))
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        logger.info("✅ Similarity search completed",
                   query=request.query[:50],
                   results_count=len(search_results),
                   processing_time_ms=processing_time,
                   user_id=current_user.id)
        
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
        documents = await Document.get_by_user(
            db, 
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        # Get actual total count for proper pagination
        total_count = await Document.count_by_user(db, user_id=current_user.id)
        
        return {
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "content_length": len(doc.content),
                    "metadata": doc.metadata,
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
        
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return {
            "id": document.id,
            "title": document.title,
            "content": document.content,
            "metadata": document.metadata,
            "created_at": document.created_at.isoformat(),
            "embeddings": [
                {
                    "id": emb.id,
                    "chunk_index": emb.chunk_index,
                    "chunk_text": emb.chunk_text[:200] + "..." if len(emb.chunk_text) > 200 else emb.chunk_text,
                    "metadata": emb.metadata
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
        
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
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
        stats = await Document.get_user_stats(db, current_user.id)
        
        return {
            "user_id": current_user.id,
            "total_documents": stats.get("total_documents", 0),
            "total_embeddings": stats.get("total_embeddings", 0),
            "total_content_length": stats.get("total_content_length", 0),
            "average_chunk_size": stats.get("average_chunk_size", 0),
            "last_indexed": stats.get("last_indexed")
        }
        
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