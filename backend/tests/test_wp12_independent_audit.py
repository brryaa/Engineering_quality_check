import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.core.auth import get_current_user
from app.models.models import Program, Part, DVPR, EngineeringIssue, EngineeringChange, RootCauseAnalysis, User


@pytest.fixture
def audit_client():
    admin = User(id=1, username="admin", role="admin", is_active=True, email="admin@audit.local", full_name="Admin", department="Audit")
    app.dependency_overrides[get_current_user] = lambda: admin
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def test_setup():
    db = SessionLocal()
    # Create isolated test entities
    p = Program(
        code="AUDIT-P1",
        name="Audit Vehicle Program",
        platform="AUDIT-ARCH",
        phase="Proto-A",
        lead_engineer="Audit Lead",
        quality_manager="Audit QM"
    )
    db.add(p)
    db.flush()

    pt = Part(
        program_id=p.id,
        part_number="AUDIT-SEAL-01",
        name="Audit Primary Seal",
        subsystem="Primary Body Seal",
        category="EPDM",
        supplier="Audit Supplier",
        material="EPDM Sponge",
        revision="A.0",
        weight_kg=1.1,
        safety_critical=True
    )
    db.add(pt)
    db.flush()

    dv = DVPR(
        program_id=p.id,
        part_id=pt.id,
        plan_code="AUDIT-DVP-01",
        test_phase="DV-A",
        test_name="High Pressure Seal Spray",
        test_standard="ISO 20653",
        acceptance_criteria="No water ingress",
        sample_size=3,
        test_facility="Audit Lab #1",
        planned_start_date="2026-10-01",
        planned_end_date="2026-10-30",
        status="Blocked",
        responsible_engineer="Audit Eng"
    )
    db.add(dv)
    db.flush()

    iss = EngineeringIssue(
        program_id=p.id,
        part_id=pt.id,
        issue_code="AUDIT-ISS-01",
        title="Corner seal gap defect",
        description="Water ingress during rain audit",
        occurrence_phase="Proto-A",
        severity="S1-Critical",
        status="Closed",
        due_date="2026-11-01",
        closure_date="2026-10-25",
        reporter="Audit Inspector",
        assignee="Audit Engineer"
    )
    db.add(iss)
    db.flush()

    ch = EngineeringChange(
        change_code="AUDIT-ECR-01",
        program_id=p.id,
        part_id=pt.id,
        title="Seal profile lip stiffener",
        change_type="Design-Mod",
        reason="Prevent water seepage",
        pre_change_rev="A.0",
        post_change_rev="A.1",
        cost_impact_rmb=4.5,
        tooling_lead_weeks=2,
        approval_status="Draft",
        initiator="Audit Engineer"
    )
    db.add(ch)
    db.commit()

    yield {
        "program_id": p.id,
        "part_id": pt.id,
        "dvpr_id": dv.id,
        "issue_id": iss.id,
        "change_id": ch.id
    }

    # Cleanup
    db.query(RootCauseAnalysis).filter(RootCauseAnalysis.issue_id == iss.id).delete()
    db.query(EngineeringChange).filter(EngineeringChange.program_id == p.id).delete()
    db.query(DVPR).filter(DVPR.program_id == p.id).delete()
    db.query(EngineeringIssue).filter(EngineeringIssue.program_id == p.id).delete()
    db.query(Part).filter(Part.program_id == p.id).delete()
    db.query(Program).filter(Program.id == p.id).delete()
    db.commit()
    db.close()


# ================= MODULE 8 AUDIT: ENGINEERING CHANGES =================
def test_audit_ecr_cannot_jump_from_draft_to_implemented(audit_client, test_setup):
    """Adversarial Scenario 1: Transitioning directly from Draft to Implemented must be rejected."""
    change_id = test_setup["change_id"]
    res = audit_client.put(f"/api/v1/changes/{change_id}", json={
        "approval_status": "Implemented"
    })
    assert res.status_code == 400
    err = res.json().get("error") or res.json().get("detail", "")
    assert "Must be Approved first" in err


def test_audit_ecr_cannot_have_identical_revisions(audit_client, test_setup):
    """Adversarial Scenario 2: ECR cannot propose identical pre and post revisions."""
    res = audit_client.post("/api/v1/changes", json={
        "change_code": "AUDIT-ECR-IDENTICAL-REV",
        "program_id": test_setup["program_id"],
        "part_id": test_setup["part_id"],
        "title": "No-op change",
        "change_type": "Design-Mod",
        "reason": "Test identical revs",
        "pre_change_rev": "A.0",
        "post_change_rev": "A.0",
        "cost_impact_rmb": 0.0,
        "tooling_lead_weeks": 0,
        "approval_status": "Draft",
        "initiator": "Audit Eng"
    })
    assert res.status_code == 400
    err = res.json().get("error") or res.json().get("detail", "")
    assert "post_change_rev must differ from pre_change_rev" in err


# ================= MODULE 5 AUDIT: DVP&R & TEST INTEGRITY =================
def test_audit_test_run_cannot_execute_against_blocked_plan(audit_client, test_setup):
    """Adversarial Scenario 3: Test execution against a Blocked verification plan must be rejected."""
    dvpr_id = test_setup["dvpr_id"]
    res = audit_client.post("/api/v1/tests", json={
        "dvpr_id": dvpr_id,
        "run_number": "AUDIT-RUN-BLOCKED-01",
        "sample_id": "SAMPLE-AUDIT-01",
        "test_date": "2026-10-25",
        "test_facility": "Chamber #1",
        "temperature_c": 25.0,
        "humidity_rh": 50.0,
        "cycles_completed": 1000,
        "result": "Pass",
        "operator": "Audit Operator",
        "measurement_data": '{"pressure_bar": 100}'
    })
    assert res.status_code == 400
    err = res.json().get("error") or res.json().get("detail", "")
    assert "Blocked DVP&R plan" in err


def test_audit_test_run_rejects_corrupted_telemetry(audit_client, test_setup):
    """Adversarial Scenario 4: Corrupted non-JSON telemetry must be rejected."""
    # First unblock plan
    db = SessionLocal()
    dv = db.query(DVPR).filter(DVPR.id == test_setup["dvpr_id"]).first()
    dv.status = "In Progress"
    db.commit()
    db.close()

    res = audit_client.post("/api/v1/tests", json={
        "dvpr_id": test_setup["dvpr_id"],
        "run_number": "AUDIT-RUN-CORRUPT-JSON",
        "sample_id": "SAMPLE-AUDIT-02",
        "test_date": "2026-10-25",
        "test_facility": "Chamber #1",
        "temperature_c": 25.0,
        "humidity_rh": 50.0,
        "cycles_completed": 1000,
        "result": "Pass",
        "operator": "Audit Operator",
        "measurement_data": "CORRUPTED_NOT_JSON_{unbalanced_bracket"
    })
    assert res.status_code == 400
    err = res.json().get("error") or res.json().get("detail", "")
    assert "valid JSON" in err


# ================= MODULE 7 AUDIT: 5-WHY ROOT CAUSE CLOSED-LOOP =================
def test_audit_root_cause_cannot_be_added_to_closed_issue(audit_client, test_setup):
    """Adversarial Scenario 5: Root cause analysis cannot be created for an already Closed issue."""
    issue_id = test_setup["issue_id"]
    res = audit_client.post("/api/v1/root-cause", json={
        "issue_id": issue_id,
        "analysis_method": "5-Why",
        "direct_cause": "Audit seal lip tear",
        "why_1": "Tooling knife worn",
        "why_2": "Sharpening cycle missed",
        "systemic_root_cause": "PM maintenance checklist missing cutter inspection",
        "verification_method": "Inspect cutter wear",
        "verification_result": "Confirmed",
        "analyst": "Audit Lead",
        "analyzed_at": "2026-10-25"
    })
    assert res.status_code == 400
    err = res.json().get("error") or res.json().get("detail", "")
    assert "already Closed issue" in err


def test_audit_deleting_root_cause_reverts_verified_issue_status(audit_client, test_setup):
    """Adversarial Scenario 6: Deleting verified root cause reverts issue status back to Investigating."""
    # Reopen issue
    db = SessionLocal()
    iss = db.query(EngineeringIssue).filter(EngineeringIssue.id == test_setup["issue_id"]).first()
    iss.status = "Investigating"
    db.commit()
    db.close()

    # Create verified root cause
    res = audit_client.post("/api/v1/root-cause", json={
        "issue_id": test_setup["issue_id"],
        "analysis_method": "5-Why",
        "direct_cause": "Audit seal lip tear",
        "why_1": "Tooling knife worn",
        "systemic_root_cause": "PM maintenance checklist missing cutter inspection",
        "verification_method": "Inspect cutter wear",
        "verification_result": "Confirmed",
        "analyst": "Audit Lead",
        "analyzed_at": "2026-10-25"
    })
    assert res.status_code == 201
    rc_id = res.json()["id"]

    # Verify issue advanced to RootCauseVerified
    iss_res = audit_client.get(f"/api/v1/issues/{test_setup['issue_id']}")
    assert iss_res.json()["status"] == "RootCauseVerified"

    # Delete root cause
    del_res = audit_client.delete(f"/api/v1/root-cause/{rc_id}")
    assert del_res.status_code == 204

    # Verify issue reverted back to Investigating
    iss_res_after = audit_client.get(f"/api/v1/issues/{test_setup['issue_id']}")
    assert iss_res_after.json()["status"] == "Investigating"
    assert iss_res_after.json()["status"] == "Investigating"
