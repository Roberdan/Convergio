"""
📚 Convergio - Document and Embedding Models (No Auth Version)
SQLAlchemy 2.0 models for vector search functionality - no user authentication required
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Integer, String, Text, JSON, Boolean, DateTime, func, text, ForeignKey
from pgvector.sqlalchemy import Vector
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from ..core.database import Base


class Document(Base):
    """Document model for vector search indexing - no user auth required"""
    
    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}
    
    # Primary key with auto-increment
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Document fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    doc_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Status fields
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    index_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now()
    )
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # # Relationships
    # embeddings: Mapped[List["DocumentEmbedding"]] = relationship(
    #     "src.models.document.DocumentEmbedding", 
    #     back_populates="document",
    #     cascade="all, delete-orphan"
    # )
    

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title[:50]}...')>"
    
    # Class methods for database operations
    @classmethod
    async def get_by_id(cls, db: AsyncSession, document_id: int) -> Optional["Document"]:
        """Get document by ID with embeddings"""
        result = await db.execute(
            select(cls)
            .options(selectinload(cls.embeddings))
            .where(cls.id == document_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_all(
        cls, 
        db: AsyncSession, 
        skip: int = 0,
        limit: int = 100
    ) -> List["Document"]:
        """Get all documents (no user filtering needed)"""
        result = await db.execute(
            select(cls)
            .options(selectinload(cls.embeddings))
            .offset(skip)
            .limit(limit)
            .order_by(cls.created_at.desc())
        )
        return result.scalars().all()
    
    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> "Document":
        """Create new document"""
        document = cls(**kwargs)
        db.add(document)
        await db.flush()
        await db.refresh(document)
        return document
    
    async def save(self, db: AsyncSession) -> None:
        """Save document changes"""
        self.updated_at = datetime.utcnow()
        db.add(self)
        await db.flush()
        await db.refresh(self)
    
    async def delete(self, db: AsyncSession) -> None:
        """Delete document and associated embeddings"""
        await db.delete(self)
        await db.flush()
    
    async def mark_indexed(self, db: AsyncSession) -> None:
        """Mark document as successfully indexed"""
        self.is_indexed = True
        self.index_status = "completed"
        self.indexed_at = datetime.utcnow()
        await self.save(db)
    
    @classmethod
    async def get_stats(cls, db: AsyncSession) -> Dict[str, Any]:
        """Get general document statistics"""
        
        # Get document count and total content length
        result = await db.execute(
            select(
                func.count(cls.id).label("total_documents"),
                func.sum(func.length(cls.content)).label("total_content_length"),
                func.max(cls.created_at).label("last_indexed")
            )
        )
        
        stats = result.first()
        
        # Get embeddings count
        embeddings_result = await db.execute(
            select(func.count(DocumentEmbedding.id))
            .join(cls)
        )
        
        total_embeddings = embeddings_result.scalar() or 0
        
        # Calculate average chunk size
        avg_chunk_result = await db.execute(
            select(func.avg(func.length(DocumentEmbedding.chunk_text)))
            .join(cls)
        )
        
        average_chunk_size = int(avg_chunk_result.scalar() or 0)
        
        return {
            "total_documents": stats.total_documents or 0,
            "total_embeddings": total_embeddings,
            "total_content_length": stats.total_content_length or 0,
            "average_chunk_size": average_chunk_size,
            "last_indexed": stats.last_indexed.isoformat() if stats.last_indexed else None
        }
    
    @classmethod
    async def count_by_user(cls, db: AsyncSession, user_id: int) -> int:
        """Count documents for a specific user"""
        result = await db.execute(
            select(func.count(cls.id)).where(cls.user_id == user_id)
        )
        return result.scalar() or 0
    
    @classmethod
    async def count_total(cls, db: AsyncSession) -> int:
        """Count total documents in database"""
        result = await db.execute(select(func.count(cls.id)))
        return result.scalar() or 0
    
    @classmethod
    async def get_first(cls, db: AsyncSession) -> Optional["Document"]:
        """Get the first document for testing purposes"""
        result = await db.execute(select(cls).limit(1))
        return result.scalar_one_or_none()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "metadata": self.doc_metadata,
            "is_indexed": self.is_indexed,
            "index_status": self.index_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
        }


class DocumentEmbedding(Base):
    """Document embedding model for vector search"""
    
    __tablename__ = "document_embeddings"
    __table_args__ = {'extend_existing': True}
    
    from sqlalchemy import Identity
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, server_default=Identity(always=False)
)
    
    # Foreign key to Document
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    
    # Chunk information
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Vector embedding (pgvector) - default 1536 dims for text-embedding-ada-002
    embedding: Mapped[List[float]] = mapped_column(Vector, nullable=False)
    
    # Metadata
    embed_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    #document: Mapped[Document] = relationship("src.models.document.Document", back_populates="embeddings")
    
    def __repr__(self) -> str:
        return f"<DocumentEmbedding(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
    
    # Class methods for database operations
    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> "DocumentEmbedding":
        """Create new document embedding"""
        embedding = cls(**kwargs)
        db.add(embedding)
        await db.flush()
        await db.refresh(embedding)
        return embedding
    
    @classmethod
    async def similarity_search(
        cls,
        db: AsyncSession,
        query_embedding: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List["DocumentEmbedding"]:
        """Perform cosine similarity search"""
        
        # Build the query
        query = select(cls).join(Document)
        
        # Apply metadata filters if provided
        if filter_metadata:
            for key, value in filter_metadata.items():
                query = query.where(cls.embed_metadata[key].astext == str(value))
        
        # Use pgvector cosine similarity with proper SQL
        from sqlalchemy import func, text
        
        # Convert query embedding to PostgreSQL array format
        embedding_array = f"[{','.join(map(str, query_embedding))}]"
        
        # Use pgvector cosine distance operator (<=>)
        # Note: cosine distance = 1 - cosine similarity
        query = query.add_columns(
            (1 - func.cast(cls.embedding, text("vector")) 
             .op("<=>")(func.cast(text(f"'{embedding_array}'"), text("vector"))))
             .label("similarity")
        ).order_by(
            func.cast(cls.embedding, text("vector"))
            .op("<=>")(func.cast(text(f"'{embedding_array}'"), text("vector")))
        ).limit(top_k)
        
        result = await db.execute(query)
        
        # Process results with actual similarity scores
        results = []
        for embedding in result.scalars().all():
            try:
                import numpy as np
                embedding_vector = np.array(embedding.embedding)
                query_vector = np.array(query_embedding)
                similarity = np.dot(embedding_vector, query_vector) / (
                    np.linalg.norm(embedding_vector) * np.linalg.norm(query_vector)
                )
                embedding.similarity_score = float(similarity)
                if similarity >= similarity_threshold:
                    results.append(embedding)
            except Exception:
                # Skip if similarity calculation fails
                continue
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: getattr(x, 'similarity_score', 0), reverse=True)
        return results[:top_k]
    
    @classmethod
    async def get_by_document(cls, db: AsyncSession, document_id: int) -> List["DocumentEmbedding"]:
        """Get all embeddings for a document"""
        result = await db.execute(
            select(cls)
            .where(cls.document_id == document_id)
            .order_by(cls.chunk_index)
        )
        return result.scalars().all()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert embedding to dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
            "metadata": self.embed_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "similarity_score": getattr(self, "similarity_score", None)
        }