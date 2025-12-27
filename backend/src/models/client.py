"""
🏢 Convergio - Client Model  
SQLAlchemy 2.0 Client model matching existing database schema
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Integer, String, DateTime, func, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Client(Base):
    """Client model matching the existing Convergio database schema"""
    
    __tablename__ = "clients"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Client info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert client to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    async def get_all(cls, db: AsyncSession, skip: int = 0, limit: int = 100) -> List["Client"]:
        """Get all clients"""
        result = await db.execute(
            select(cls)
            .offset(skip)
            .limit(limit)
            .order_by(cls.created_at.desc())
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, client_id: int) -> Optional["Client"]:
        """Get client by ID"""
        result = await db.execute(
            select(cls).where(cls.id == client_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_total_count(cls, db: AsyncSession) -> int:
        """Get total count of clients"""
        result = await db.execute(
            select(func.count(cls.id))
        )
        return result.scalar() or 0