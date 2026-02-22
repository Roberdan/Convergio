"""Prisma-aligned SQLAlchemy models (read-only ORM mapping)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Tier(Base):
    __tablename__ = "Tier"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    maxAgents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maxConversations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    features: Mapped[list["TierFeature"]] = relationship(back_populates="tier")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="tier")
    trialSessions: Mapped[list["TrialSession"]] = relationship(back_populates="tier")


class TierFeature(Base):
    __tablename__ = "TierFeature"
    __table_args__ = (UniqueConstraint("tierId", "key", name="TierFeature_tierId_key_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tierId: Mapped[UUID] = mapped_column(ForeignKey("Tier.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String)
    value: Mapped[str] = mapped_column(String)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())

    tier: Mapped[Tier] = relationship(back_populates="features")


class Subscription(Base):
    __tablename__ = "Subscription"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tierId: Mapped[UUID] = mapped_column(ForeignKey("Tier.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

    tier: Mapped[Tier] = relationship(back_populates="subscriptions")


class TrialSession(Base):
    __tablename__ = "TrialSession"
    __table_args__ = (UniqueConstraint("tierId", "email", name="TrialSession_tierId_email_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tierId: Mapped[UUID] = mapped_column(ForeignKey("Tier.id", ondelete="RESTRICT"), nullable=False)
    email: Mapped[str] = mapped_column(String)
    startedAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    endsAt: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    tier: Mapped[Tier] = relationship(back_populates="trialSessions")


class Team(Base):
    __tablename__ = "Team"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())

    members: Mapped[list["TeamMember"]] = relationship(back_populates="team")
    invites: Mapped[list["Invite"]] = relationship(back_populates="team")


class TeamMember(Base):
    __tablename__ = "TeamMember"
    __table_args__ = (UniqueConstraint("teamId", "email", name="TeamMember_teamId_email_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    teamId: Mapped[UUID] = mapped_column(ForeignKey("Team.id", ondelete="CASCADE"), nullable=False)
    userId: Mapped[UUID | None] = mapped_column(nullable=True)
    agentId: Mapped[UUID | None] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, server_default="member")
    type: Mapped[str] = mapped_column(String, server_default="HUMAN")
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())

    team: Mapped[Team] = relationship(back_populates="members")


class Invite(Base):
    __tablename__ = "Invite"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    teamId: Mapped[UUID] = mapped_column(ForeignKey("Team.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String)
    token: Mapped[str] = mapped_column(String, unique=True)
    role: Mapped[str] = mapped_column(String, server_default="member")
    status: Mapped[str] = mapped_column(String, server_default="pending")
    type: Mapped[str] = mapped_column(String, server_default="human")
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    expiresAt: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    team: Mapped[Team] = relationship(back_populates="invites")


class AdminAuditLog(Base):
    __tablename__ = "AdminAuditLog"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String)
    actor: Mapped[str] = mapped_column(String)
    payload: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())


class ComplianceAuditEntry(Base):
    __tablename__ = "ComplianceAuditEntry"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    payload: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    occurredAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())


class WaitlistRequest(Base):
    __tablename__ = "WaitlistRequest"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    metadata: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())


class Session(Base):
    __tablename__ = "Session"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String, unique=True)
    userId: Mapped[str | None] = mapped_column(String, nullable=True)
    expiresAt: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
