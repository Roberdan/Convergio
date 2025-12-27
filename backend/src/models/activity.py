"""
📋 Convergio - Activity Model  
SQLAlchemy 2.0 Activity model matching existing database schema
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Integer, String, DateTime, func, Text, BigInteger, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Activity(Base):
    """Activity model matching the existing Convergio database schema"""
    
    __tablename__ = "activities"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # Foreign key to engagement
    engagement_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("engagements.id"), nullable=True)
    
    # Activity info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Vector embeddings - existing in DB
    # NOTE: In dev environments vector column may not be available; use nullable with server_default NULL
    description_embedding: Mapped[Optional[bytes]] = mapped_column(nullable=True)
    context_embedding: Mapped[Optional[bytes]] = mapped_column(nullable=True)
    requirements_embedding: Mapped[Optional[bytes]] = mapped_column(nullable=True)
    
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
    
    # Relationship back to engagement
    engagement: Mapped[Optional["Engagement"]] = relationship("Engagement", back_populates="activities")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.get_status(),
            "progress": self.calculate_progress()
        }
    
    def get_status(self) -> str:
        """Calculate activity status based on dates"""
        now = datetime.utcnow()
        if self.created_at:
            days_old = (now - self.created_at.replace(tzinfo=None)).days
            if days_old < 1:
                return "backlog"
            elif days_old < 3:
                return "planning"
            elif days_old < 10:
                return "in_progress"
            elif days_old < 20:
                return "review"
            else:
                return "done"
        return "planning"
    
    def calculate_progress(self) -> float:
        """Calculate progress percentage based on age"""
        now = datetime.utcnow()
        if self.created_at:
            days_old = (now - self.created_at.replace(tzinfo=None)).days
            # Simple progress calculation: newer activities have lower progress
            if days_old < 20:
                return min(days_old * 5.0, 100.0)  # 5% per day for first 20 days
            else:
                return 100.0
        return 0.0
    
    @classmethod
    async def get_all(cls, db: AsyncSession, skip: int = 0, limit: int = 100) -> List["Activity"]:
        """Get all activities"""
        result = await db.execute(
            select(cls)
            .offset(skip)
            .limit(limit)
            .order_by(cls.created_at.desc())
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, activity_id: int) -> Optional["Activity"]:
        """Get activity by ID"""
        result = await db.execute(
            select(cls).where(cls.id == activity_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_total_count(cls, db: AsyncSession) -> int:
        """Get total count of activities"""
        result = await db.execute(
            select(func.count(cls.id))
        )
        return result.scalar() or 0
    
    @classmethod
    async def get_recent(cls, db: AsyncSession, limit: int = 10) -> List["Activity"]:
        """Get recent activities"""
        result = await db.execute(
            select(cls)
            .order_by(cls.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_for_engagement(cls, db: AsyncSession, engagement_id: int, limit: int = 10) -> List["Activity"]:
        """Get activities for a specific engagement (simplified logic for now)"""
        # For now, we'll return activities based on a hash-like relationship
        # In a real system, you'd have a proper junction table
        activities = await cls.get_all(db, limit=50)
        
        # Simple distribution: each engagement gets activities based on its ID
        activities_per_engagement = 3
        start_idx = ((engagement_id - 1) * activities_per_engagement) % len(activities)
        end_idx = min(start_idx + activities_per_engagement, len(activities))
        
        return activities[start_idx:end_idx] if activities else []