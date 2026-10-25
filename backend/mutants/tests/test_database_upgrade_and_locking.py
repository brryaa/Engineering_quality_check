import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError
from app.core.database import Base
from app.models.models import Program, Part, EngineeringIssue, EngineeringChange


def create_sample_program(code: str, name: str) -> Program:
    return Program(
        code=code,
        name=name,
        platform="P-CLOSURE",
        phase="DV",
        lead_engineer="Chief Door Engineer",
        quality_manager="Quality Lead",
        target_market="Global"
    )


def test_sqlite_foreign_key_integrity(db_session):
    """Verify that foreign keys are enforced by SQLite engine."""
    # Attempt to create a part pointing to a non-existent program_id
    invalid_part = Part(
        program_id=999999,
        part_number="TEST-INVALID-FK",
        name="Invalid Part",
        subsystem="Front Door Closure",
        category="Stamping",
        material="Steel",
        supplier="Test Supplier",
        weight_kg=1.0,
        revision="A.0"
    )
    db_session.add(invalid_part)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_optimistic_locking_issue_conflict(db_session):
    """Verify optimistic locking prevents lost updates via version_id on EngineeringIssue."""
    # 1. Create a program and part
    prog = create_sample_program("TEST-OPT-1", "Opt Locking Program")
    db_session.add(prog)
    db_session.commit()
    db_session.refresh(prog)

    part = Part(
        program_id=prog.id,
        part_number="OPT-PART-01",
        name="Opt Part",
        subsystem="Front Door Closure",
        category="Stamping",
        material="Steel",
        supplier="Test",
        weight_kg=2.5,
        revision="A"
    )
    db_session.add(part)
    db_session.commit()
    db_session.refresh(part)

    # 2. Create an issue with version_id = 1
    issue = EngineeringIssue(
        issue_code="OPT-ISS-001",
        program_id=prog.id,
        part_id=part.id,
        title="Original Issue Title",
        severity="S2-Major",
        status="New",
        description="Initial description",
        occurrence_phase="DV-Testing",
        assignee="Alice",
        reporter="Bob",
        due_date="2026-12-31"
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)
    assert issue.version_id == 1

    # 3. Simulate two concurrent sessions fetching the same issue
    Session = sessionmaker(bind=db_session.get_bind())
    session_a = Session()
    session_b = Session()

    issue_a = session_a.query(EngineeringIssue).filter_by(id=issue.id).first()
    issue_b = session_b.query(EngineeringIssue).filter_by(id=issue.id).first()

    # User A updates issue title
    issue_a.title = "User A Updated Title"
    session_a.commit()
    assert issue_a.version_id == 2

    # User B (holding stale version_id = 1) attempts to update issue title
    issue_b.title = "User B Conflicting Update"
    with pytest.raises(StaleDataError):
        session_b.commit()
    session_b.rollback()

    session_a.close()
    session_b.close()


def test_optimistic_locking_change_conflict(db_session):
    """Verify optimistic locking on EngineeringChange."""
    prog = create_sample_program("TEST-OPT-2", "Change Locking Program")
    db_session.add(prog)
    db_session.commit()

    part = Part(
        program_id=prog.id,
        part_number="OPT-PART-02",
        name="Opt Part 2",
        subsystem="Front Door Closure",
        category="Stamping",
        material="Steel",
        supplier="Test",
        weight_kg=2.0,
        revision="A"
    )
    db_session.add(part)
    db_session.commit()

    ecr = EngineeringChange(
        change_code="ECR-OPT-001",
        program_id=prog.id,
        part_id=part.id,
        title="Initial ECR",
        change_type="Design-Mod",
        reason="Optimistic lock test",
        pre_change_rev="A",
        post_change_rev="B",
        initiator="Engineer 1"
    )
    db_session.add(ecr)
    db_session.commit()
    db_session.refresh(ecr)
    assert ecr.version_id == 1

    Session = sessionmaker(bind=db_session.get_bind())
    session_a = Session()
    session_b = Session()

    ecr_a = session_a.query(EngineeringChange).filter_by(id=ecr.id).first()
    ecr_b = session_b.query(EngineeringChange).filter_by(id=ecr.id).first()

    ecr_a.title = "Updated by Approver A"
    session_a.commit()
    assert ecr_a.version_id == 2

    ecr_b.title = "Conflicting update by Approver B"
    with pytest.raises(StaleDataError):
        session_b.commit()
    session_b.rollback()

    session_a.close()
    session_b.close()


def test_transaction_rollback_atomic_guarantee(db_session):
    """Verify atomicity: partial failure rolls back entire transaction."""
    prog = create_sample_program("TEST-ATOMIC-1", "Atomic Program")
    db_session.add(prog)
    db_session.commit()

    try:
        # Part 1 succeeds
        p1 = Part(program_id=prog.id, part_number="ATM-P1", name="P1", subsystem="Front Door Closure", category="Stamping", material="Steel", supplier="S", weight_kg=1.0, revision="A")
        db_session.add(p1)

        # Part 2 fails unique constraint on part_number
        p2_dupe = Part(program_id=prog.id, part_number="ATM-P1", name="P2 Duplicate", subsystem="Front Door Closure", category="Stamping", material="Steel", supplier="S", weight_kg=1.0, revision="A")
        db_session.add(p2_dupe)

        db_session.commit()
    except IntegrityError:
        db_session.rollback()

    # Verify p1 was NOT persisted
    found = db_session.query(Part).filter_by(part_number="ATM-P1").first()
    assert found is None
