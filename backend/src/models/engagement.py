"""
📋 Convergio - Engagement/Project Model

SQLAlchemy 2.0 Engagement model matching existing database schema.
This model represents projects/engagements in the Convergio system.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Integer, String, DateTime, func, Text, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base
# Ensure Activity mapper is registered so relationship string resolves during mapper setup
from .activity import Activity  # noqa: F401


class Engagement(Base):
    """
    Engagement/Project model matching the existing Convergio database schema.
    
    Represents a project or engagement that can contain multiple activities
    and be managed through the project management interface.
    """
    
    __tablename__ = "engagements"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)#, index=True)
    
    # Engagement information
    title: Mapped[str] = mapped_column(String(255), nullable=False)#, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status and progress tracking
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="planning")
    progress: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        onupdate=func.now(), 
        nullable=True
    )
    
    # Relationships
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", 
        back_populates="engagement",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the engagement."""
        return f"<Engagement(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    def get_status(self) -> str:
        """Get the current status of the engagement."""
        return self.status or "planning"
    
    def get_progress(self) -> float:
        """Get the current progress percentage."""
        return self.progress or 0.0
    
    def is_active(self) -> bool:
        """Check if the engagement is currently active."""
        return self.status in ["planning", "in_progress"]
    
    def is_completed(self) -> bool:
        """Check if the engagement is completed."""
        return self.status == "completed"
    
    def is_on_hold(self) -> bool:
        """Check if the engagement is on hold."""
        return self.status == "on_hold"
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, engagement_id: int) -> Optional["Engagement"]:
        """Get an engagement by its ID."""
        result = await db.execute(
            select(cls).where(cls.id == engagement_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_all_active(cls, db: AsyncSession) -> List["Engagement"]:
        """Get all active engagements."""
        result = await db.execute(
            select(cls).where(cls.status.in_(["planning", "in_progress"]))
        )
        return result.scalars().all()
    
    @classmethod
    async def get_by_status(cls, db: AsyncSession, status: str) -> List["Engagement"]:
        """Get engagements by status."""
        result = await db.execute(
            select(cls).where(cls.status == status)
        )
        return result.scalars().all()
    
    @classmethod
    async def search_by_title(cls, db: AsyncSession, search_term: str) -> List["Engagement"]:
        """Search engagements by title."""
        result = await db.execute(
            select(cls).where(cls.title.ilike(f"%{search_term}%"))
        )
        return result.scalars().all()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engagement to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.get_status(),
            "progress": self.get_progress(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "activities_count": 0  # Will be populated separately when needed
        }