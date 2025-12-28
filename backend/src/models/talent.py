"""
👥 Convergio - Talent Model (No Auth Version)
SQLAlchemy 2.0 Talent model with organizational hierarchy - no authentication required
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from decimal import Decimal
from sqlalchemy import Integer, String, DateTime, func, Boolean, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from ..core.database import Base


class Talent(Base):
    """Talent model matching the existing Convergio database schema"""
    
    __tablename__ = "talents"
    __table_args__ = {'extend_existing': True}
    
    # id, first_name, last_name, email, phone, location, department, role,skills, experience_years, bio, is_active, rating, metadata, created_at, updated_at

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)#, index=True)
    
    # Basic info - matching existing schema
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)#, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    department: Mapped[Optional[str]] = mapped_column(String(512))
    # Legacy fields - matching existing schema
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Legacy field
    is_admin: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)      # Legacy field
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # Legacy field

    # WS2: New People Data Model fields
    role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Job title/role
    tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Seniority: junior, mid, senior, lead, principal
    skills: Mapped[Optional[Dict]] = mapped_column(JSONB, default=list, nullable=True)  # Skills array
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # USD
    daily_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # USD
    availability: Mapped[Optional[int]] = mapped_column(Integer, default=100, nullable=True)  # 0-100%
    timezone: Mapped[Optional[str]] = mapped_column(String(100), default='UTC', nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    experience_years: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), default=0.00, nullable=True)

    # Vector embeddings - existing in DB (pgvector)
    # Use explicit pgvector type to avoid BYTEA casts on NULL that break inserts
    skills_embedding: Mapped[Optional[list]] = mapped_column(Vector(1536), nullable=True)
    experience_embedding: Mapped[Optional[list]] = mapped_column(Vector(1536), nullable=True)
    profile_embedding: Mapped[Optional[list]] = mapped_column(Vector(1536), nullable=True)
    
    # Timestamps - matching existing schema
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),  # existing schema uses timestamp without time zone
        server_default=func.now(),
        nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),  # existing schema uses timestamp without time zone
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )

    
    @property
    def full_name(self) -> str:
        """Get full name from first and last name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]  # Use email username as fallback
    
    @property 
    def username(self) -> str:
        """Get username from email for compatibility"""
        return self.email.split('@')[0] if self.email else "unknown"

    
    
    @property
    def is_active(self) -> bool:
        """Check if talent is active (not deleted)"""
        return self.deleted_at is None
    
    @classmethod
    async def get_all(
        cls, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List["Talent"]:
        """Get all talents with filtering"""
        
        query = select(cls)
        
        # Apply active filter (using deleted_at)
        if is_active is True:
            query = query.where(cls.deleted_at.is_(None))
        elif is_active is False:
            query = query.where(cls.deleted_at.is_not(None))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, talent_id: int) -> Optional["Talent"]:
        """Get talent by ID"""
        
        query = select(cls).where(cls.id == talent_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_username(cls, db: AsyncSession, username: str) -> Optional["Talent"]:
        """Get talent by username (using email prefix)"""
        
        # Search for email that starts with username@
        query = select(cls).where(cls.email.like(f"{username}@%"))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_department(cls, db: AsyncSession, department: str) -> Optional["Talent"]:
        """Get talent by department (using department name)"""
        query = select(cls).where(cls.department==department)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Optional["Talent"]:
        """Get talent by email"""
        
        query = select(cls).where(cls.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> "Talent":
        """Create new talent"""
        
        talent = cls(**kwargs)
        db.add(talent)
        await db.commit()
        await db.refresh(talent)
        return talent
    
    async def save(self, db: AsyncSession):
        """Save talent changes"""
        
        await db.commit()
        await db.refresh(self)
    
    async def update(self, db: AsyncSession, data: Dict[str, Any]):
        """Update talent with provided data"""
        
        for field, value in data.items():
            if hasattr(self, field) and value is not None:
                setattr(self, field, value)
        
        await self.save(db)
    
    @classmethod
    async def get_subordinates(cls, db: AsyncSession, manager_id: int) -> List["Talent"]:
        """Get all subordinates of a manager - not supported in current schema"""
        
        # Current database schema doesn't have manager_id
        return []
    
    @classmethod
    async def get_hierarchy(cls, db: AsyncSession, talent_id: int) -> Dict[str, Any]:
        """Get talent hierarchy - simplified for current schema"""
        
        talent = await cls.get_by_id(db, talent_id)
        if not talent:
            return {}
        
        return {
            "talent": {
                "id": talent.id,
                "username": talent.username,
                "email": talent.email,
                "full_name": talent.full_name,
                "is_admin": talent.is_admin
            },
            "managers": [],  # No manager hierarchy in current schema
            "subordinates": []  # No subordinates in current schema
        }
    
    @classmethod
    async def get_total_count(cls, db: AsyncSession) -> int:
        """Get total count of all talents"""
        result = await db.execute(
            select(func.count(cls.id))
            .where(cls.deleted_at.is_(None))
        )
        return result.scalar() or 0
    
    @classmethod
    async def get_active_count(cls, db: AsyncSession, since_date=None) -> int:
        """Get count of active talents (not deleted)"""
        query = select(func.count(cls.id)).where(cls.deleted_at.is_(None))
        
        # If since_date is provided, filter by created_at or updated_at
        if since_date:
            query = query.where(
                (cls.created_at >= since_date) | (cls.updated_at >= since_date)
            )
        
        result = await db.execute(query)
        return result.scalar() or 0