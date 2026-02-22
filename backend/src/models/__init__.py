"""Convergio SQLAlchemy models package."""

__all__: list[str] = []

try:
    from .prisma_models import (
        AdminAuditLog,
        ComplianceAuditEntry,
        Invite,
        Session,
        Subscription,
        Team,
        TeamMember,
        Tier,
        TierFeature,
        TrialSession,
        WaitlistRequest,
    )

    __all__ = [
        "Tier",
        "TierFeature",
        "Subscription",
        "TrialSession",
        "Team",
        "TeamMember",
        "Invite",
        "AdminAuditLog",
        "ComplianceAuditEntry",
        "WaitlistRequest",
        "Session",
    ]
except ModuleNotFoundError:
    # Keep package importable in minimal environments without DB deps.
    pass
