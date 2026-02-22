from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.src.models.prisma_models import (
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


def _unique_sets(table):
    return {
        tuple(sorted(col.name for col in c.columns))
        for c in table.constraints
        if isinstance(c, UniqueConstraint)
    }


def _fk(table, column_name: str):
    for fk in table.foreign_key_constraints:
        if any(col.name == column_name for col in fk.columns):
            return fk
    return None


def test_prisma_table_names_and_core_columns_match_expected_schema():
    assert Tier.__tablename__ == "Tier"
    assert Team.__tablename__ == "Team"
    assert WaitlistRequest.__tablename__ == "WaitlistRequest"

    assert isinstance(Tier.__table__.c.id.type, UUID)
    assert isinstance(Tier.__table__.c.name.type, String)
    assert isinstance(Tier.__table__.c.maxAgents.type, Integer)
    assert isinstance(Tier.__table__.c.createdAt.type, DateTime)
    assert isinstance(Tier.__table__.c.updatedAt.type, DateTime)

    assert isinstance(AdminAuditLog.__table__.c.payload.type, JSONB)
    assert isinstance(ComplianceAuditEntry.__table__.c.payload.type, JSONB)
    assert isinstance(WaitlistRequest.__table__.c.metadata.type, JSONB)


def test_prisma_unique_constraints_match_schema():
    assert ("name",) in _unique_sets(Tier.__table__)
    assert tuple(sorted(["tierId", "key"])) in _unique_sets(TierFeature.__table__)
    assert tuple(sorted(["tierId", "email"])) in _unique_sets(TrialSession.__table__)
    assert tuple(sorted(["teamId", "email"])) in _unique_sets(TeamMember.__table__)
    assert ("token",) in _unique_sets(Invite.__table__)
    assert ("email",) in _unique_sets(WaitlistRequest.__table__)
    assert ("token",) in _unique_sets(Session.__table__)


def test_prisma_foreign_keys_and_ondelete_match_schema():
    tf_fk = _fk(TierFeature.__table__, "tierId")
    assert tf_fk is not None
    assert tf_fk.ondelete == "CASCADE"
    assert {e.target_fullname for e in tf_fk.elements} == {"Tier.id"}

    sub_fk = _fk(Subscription.__table__, "tierId")
    assert sub_fk is not None
    assert sub_fk.ondelete == "RESTRICT"
    assert {e.target_fullname for e in sub_fk.elements} == {"Tier.id"}

    trial_fk = _fk(TrialSession.__table__, "tierId")
    assert trial_fk is not None
    assert trial_fk.ondelete == "RESTRICT"
    assert {e.target_fullname for e in trial_fk.elements} == {"Tier.id"}

    tm_fk = _fk(TeamMember.__table__, "teamId")
    assert tm_fk is not None
    assert tm_fk.ondelete == "CASCADE"
    assert {e.target_fullname for e in tm_fk.elements} == {"Team.id"}

    invite_fk = _fk(Invite.__table__, "teamId")
    assert invite_fk is not None
    assert invite_fk.ondelete == "CASCADE"
    assert {e.target_fullname for e in invite_fk.elements} == {"Team.id"}
