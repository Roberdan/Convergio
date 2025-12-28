"""
🔗 Convergio - Project Assignment Model
Links talents and AI agents to projects with allocation and billing info
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy import Integer, String, DateTime, Date, Boolean, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func

from ..core.database import Base


class ProjectAssignment(Base):
    """Project assignment model linking resources (talents/agents) to projects"""

    __tablename__ = "project_assignments"
    __table_args__ = (
        CheckConstraint("allocation_pct >= 0 AND allocation_pct <= 100", name="check_allocation_pct"),
        CheckConstraint("resource_type IN ('talent', 'agent')", name="check_resource_type"),
        CheckConstraint("status IN ('active', 'paused', 'completed', 'cancelled')", name="check_status"),
        {'extend_existing': True}
    )

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Project reference
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    # Resource type and ID
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'talent' or 'agent'
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Allocation
    allocation_pct: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Role in project (may differ from talent's general role)
    role_in_project: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Dates
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default='active', nullable=False)

    # Billing
    billable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hourly_rate_override: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )

    # Relationships
    # project = relationship("Project", back_populates="assignments")

    @classmethod
    async def get_by_project(
        cls,
        db: AsyncSession,
        project_id: int,
        resource_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List["ProjectAssignment"]:
        """Get all assignments for a project"""

        query = select(cls).where(cls.project_id == project_id)

        if resource_type:
            query = query.where(cls.resource_type == resource_type)
        if status:
            query = query.where(cls.status == status)

        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_resource(
        cls,
        db: AsyncSession,
        resource_type: str,
        resource_id: int,
        status: Optional[str] = None
    ) -> List["ProjectAssignment"]:
        """Get all project assignments for a resource (talent or agent)"""

        query = select(cls).where(
            cls.resource_type == resource_type,
            cls.resource_id == resource_id
        )

        if status:
            query = query.where(cls.status == status)

        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_talent_projects(
        cls,
        db: AsyncSession,
        talent_id: int
    ) -> List["ProjectAssignment"]:
        """Get all active project assignments for a talent"""

        return await cls.get_by_resource(db, 'talent', talent_id, status='active')

    @classmethod
    async def get_agent_projects(
        cls,
        db: AsyncSession,
        agent_id: int
    ) -> List["ProjectAssignment"]:
        """Get all active project assignments for an agent"""

        return await cls.get_by_resource(db, 'agent', agent_id, status='active')

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> "ProjectAssignment":
        """Create new project assignment"""

        assignment = cls(**kwargs)
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    async def update(self, db: AsyncSession, data: Dict[str, Any]):
        """Update assignment with provided data"""

        for field, value in data.items():
            if hasattr(self, field) and value is not None:
                setattr(self, field, value)

        await db.commit()
        await db.refresh(self)

    async def delete(self, db: AsyncSession):
        """Delete this assignment"""

        await db.delete(self)
        await db.commit()

    @classmethod
    async def get_total_allocation(
        cls,
        db: AsyncSession,
        resource_type: str,
        resource_id: int
    ) -> int:
        """Get total allocation percentage for a resource across all active projects"""

        result = await db.execute(
            select(func.sum(cls.allocation_pct))
            .where(cls.resource_type == resource_type)
            .where(cls.resource_id == resource_id)
            .where(cls.status == 'active')
        )
        return result.scalar() or 0

    @classmethod
    async def get_available_capacity(
        cls,
        db: AsyncSession,
        resource_type: str,
        resource_id: int
    ) -> int:
        """Get remaining available capacity for a resource (100 - total allocation)"""

        total = await cls.get_total_allocation(db, resource_type, resource_id)
        return max(0, 100 - total)
