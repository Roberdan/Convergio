"""
👥 Convergio2030 - Talent Model (No Auth Version)
SQLAlchemy 2.0 Talent model with organizational hierarchy - no authentication required
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Integer, String, DateTime, func, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Talent(Base):
    """Talent model for organizational management - standalone without user auth"""
    
    __tablename__ = "talents"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Basic info (previously from User model)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Organizational fields
    position: Mapped[Optional[str]] = mapped_column(String(200))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    manager_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("talents.id"))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
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
    
    # Relationships
    manager: Mapped[Optional["Talent"]] = relationship("Talent", remote_side=[id], back_populates="subordinates")
    subordinates: Mapped[List["Talent"]] = relationship("Talent", back_populates="manager")
    
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
            return self.username
    
    @classmethod
    async def get_all(
        cls, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        department: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List["Talent"]:
        """Get all talents with filtering"""
        
        query = select(cls)
        
        # Apply filters
        if department:
            query = query.where(cls.department == department)
        if is_active is not None:
            query = query.where(cls.is_active == is_active)
        
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
        """Get talent by username"""
        
        query = select(cls).where(cls.username == username)
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
        """Get all subordinates of a manager"""
        
        query = select(cls).where(cls.manager_id == manager_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def get_hierarchy(cls, db: AsyncSession, talent_id: int) -> Dict[str, Any]:
        """Get complete hierarchy for a talent"""
        
        talent = await cls.get_by_id(db, talent_id)
        if not talent:
            return {}
        
        # Get manager chain
        managers = []
        current = talent
        while current.manager_id:
            manager = await cls.get_by_id(db, current.manager_id)
            if manager:
                managers.append({
                    "id": manager.id,
                    "username": manager.username,
                    "full_name": manager.full_name,
                    "position": manager.position,
                    "department": manager.department
                })
                current = manager
            else:
                break
        
        # Get subordinates
        subordinates = await cls.get_subordinates(db, talent_id)
        subordinates_data = [
            {
                "id": sub.id,
                "username": sub.username,
                "full_name": sub.full_name,
                "position": sub.position,
                "department": sub.department
            }
            for sub in subordinates
        ]
        
        return {
            "talent": {
                "id": talent.id,
                "username": talent.username,
                "full_name": talent.full_name,
                "position": talent.position,
                "department": talent.department
            },
            "managers": managers,
            "subordinates": subordinates_data
        }