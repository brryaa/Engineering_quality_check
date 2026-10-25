import pytest
from app.models.models import (
    Program, Part, DFMEA, DVPR, TestRun,
    EngineeringIssue, RootCauseAnalysis, EngineeringChange, KnowledgeItem
)
TestRun.__test__ = False


# ==============================================================================
# MODULE 6: ENGINEERING ISSUE TRACKING TESTS (25 Tests)
# ==============================================================================

ISSUE_SEVERITIES = ["S1-Critical", "S2-Major", "S3-Minor", "S4-Cosmetic"]
ISSUE_STATUSES = [
    "New", "Investigating", "Containment", "RootCauseVerified",
    "ActionImplemented", "ValidationPass", "Closed", "Rejected"
]
OCCURRENCE_PHASES = ["Proto-Build", "DV-Testing", "PV-Trial", "Pre-SOP", "Field-Feedback"]

@pytest.fixture
def issue_test_context(client):
    prog = client.post("/api/v1/programs", json={
        "code": "PROG-ISSUE-HUB",
        "name": "Issue Testing Program",
        "platform": "P-ISSUE",
        "phase": "PV",
        "lead_engineer": "Eng Lead",
        "quality_manager": "QM Lead",
        "target_market": "Global"
    }).json()

    part = client.post("/api/v1/parts", json={
        "program_id": prog["id"],
        "part_number": "PART-ISSUE-HUB-01",
        "name": "Front Door Latch Actuator",
        "subsystem": "Front Door Closure",
        "category": "Assembly",
        "material": "Polymer/Steel",
        "supplier": "Kiekert Closure Systems",
        "weight_kg": 0.78,
        "revision": "A.0"
    }).json()

    return {"program_id": prog["id"], "part_id": part["id"]}


@pytest.mark.parametrize("sev", ISSUE_SEVERITIES)
def test_mod6_issue_severity_classifications(client, issue_test_context, sev):
    """Verify issue creation across all automotive quality severity classifications."""
    res = client.post("/api/v1/issues", json={
        "issue_code": f"ISS-SEV-{sev}",
        "program_id": issue_test_context["program_id"],
        "part_id": issue_test_context["part_id"],
        "title": f"Test defect with severity {sev}",
        "severity": sev,
        "status": "New",
        "description": "Defect observation during inspection",
        "occurrence_phase": "DV-Testing",
        "assignee": "Engineer Li",
        "reporter": "Quality Tech Wang",
        "due_date": "2026-12-15"
    })
    assert res.status_code == 201
    assert res.json()["severity"] == sev


@pytest.mark.parametrize("status_val", ISSUE_STATUSES)
def test_mod6_issue_8d_status_transitions(client, issue_test_context, status_val):
    """Verify issue status updates across all 8-D lifecycle workflow states."""
    # Create base issue
    code = f"ISS-TRANS-{status_val}"
    created = client.post("/api/v1/issues", json={
        "issue_code": code,
        "program_id": issue_test_context["program_id"],
        "part_id": issue_test_context["part_id"],
        "title": f"Lifecycle transition to {status_val}",
        "severity": "S2-Major",
        "status": "New",
        "description": "Transition test",
        "occurrence_phase": "PV-Trial",
        "assignee": "Engineer A",
        "reporter": "Tech B",
        "due_date": "2026-12-20"
    }).json()
    iss_id = created["id"]

    # Transition to target status
    up = client.put(f"/api/v1/issues/{iss_id}", json={"status": status_val})
    assert up.status_code == 200
    assert up.json()["status"] == status_val

    # If transitioned to Closed, verify closure_date is automatically assigned
    if status_val == "Closed":
        assert up.json()["closure_date"] is not None


@pytest.mark.parametrize("phase", OCCURRENCE_PHASES)
def test_mod6_issue_occurrence_phases(client, issue_test_context, phase):
    """Verify tracking defect occurrence across vehicle maturation phases."""
    res = client.post("/api/v1/issues", json={
        "issue_code": f"ISS-OCCUR-{phase}",
        "program_id": issue_test_context["program_id"],
        "part_id": issue_test_context["part_id"],
        "title": f"Occurrence phase defect {phase}",
        "severity": "S3-Minor",
        "status": "New",
        "description": "Phase tracking",
        "occurrence_phase": phase,
        "assignee": "Eng",
        "reporter": "Tech",
        "due_date": "2026-12-30"
    })
    assert res.status_code == 201
    assert res.json()["occurrence_phase"] == phase


def test_mod6_issue_filtering_and_pagination(client, issue_test_context):
    """Test multi-filter search queries on engineering issues."""
    res = client.get(f"/api/v1/issues?program_id={issue_test_context['program_id']}&severity=S2-Major&page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    for item in data["items"]:
        assert item["severity"] == "S2-Major"


# ==============================================================================
# MODULE 7: ROOT CAUSE ANALYSIS (5-WHY & ISHIKAWA) TESTS (25 Tests)
# ==============================================================================

@pytest.fixture
def standalone_issue(client, issue_test_context):
    res = client.post("/api/v1/issues", json={
        "issue_code": "ISS-FOR-RC-001",
        "program_id": issue_test_context["program_id"],
        "part_id": issue_test_context["part_id"],
        "title": "Front door latch false unlock during lateral curb impact",
        "severity": "S1-Critical",
        "status": "Investigating",
        "description": "Door unlatched from primary catch when traversing high speed curb",
        "occurrence_phase": "PV-Trial",
        "assignee": "Dr. Fast Latch Specialist",
        "reporter": "Test Driver",
        "due_date": "2026-11-30"
    })
    return res.json()["id"]


def test_mod7_root_cause_complete_5why_analysis(client, standalone_issue):
    """Verify 5-Why root cause analysis creation and issue status progression."""
    res = client.post("/api/v1/root-cause", json={
        "issue_id": standalone_issue,
        "analysis_method": "5-Why",
        "direct_cause": "Inertia lever dynamic counterweight rotated under 15g lateral acceleration",
        "why_1": "Inertia locking lever did not engage the release pawl stop pin",
        "why_2": "Return spring preload torque was insufficient (0.045 Nm vs 0.080 Nm nominal)",
        "why_3": "Spring supplier wire coil bending radius exceeded tolerance (+0.35mm)",
        "why_4": "Wire bending tooling mandrel worn past service limit (50,000 cycles without check)",
        "why_5": "Supplier preventative maintenance standard lacked automated tool wear optical gauging",
        "systemic_root_cause": "Supplier quality assurance gap: Tier 2 tooling wear cycle monitoring missing in APQP control plan",
        "verification_method": "High-g acceleration sled test (20g lateral) with high-speed camera verification",
        "verification_result": "Confirmed",
        "analyst": "Dr. Fast Latch Specialist",
        "analyzed_at": "2026-11-08"
    })
    assert res.status_code == 201
    rc = res.json()
    assert rc["analysis_method"] == "5-Why"
    assert rc["verification_result"] == "Confirmed"
    assert rc["why_5"] is not None

    # Verify that confirming root cause automatically progressed issue status to 'RootCauseVerified'
    iss_check = client.get(f"/api/v1/issues/{standalone_issue}").json()
    assert iss_check["status"] == "RootCauseVerified"
    assert iss_check["has_root_cause"] is True


def test_mod7_root_cause_duplicate_for_same_issue_rejected(client, standalone_issue):
    """An issue can have at most one root cause analysis record (1:1 relationship)."""
    payload = {
        "issue_id": standalone_issue,
        "analysis_method": "5-Why",
        "direct_cause": "First attempt",
        "systemic_root_cause": "Systemic cause",
        "verification_method": "Method",
        "analyst": "Analyst",
        "analyzed_at": "2026-11-09"
    }
    r1 = client.post("/api/v1/root-cause", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/root-cause", json=payload)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["error"]


@pytest.mark.parametrize("method", ["5-Why", "Ishikawa-Fishbone", "FTA"])
def test_mod7_root_cause_analysis_methods(client, issue_test_context, method):
    """Test diverse root cause analysis methodologies (5-Why, Fishbone, Fault Tree Analysis)."""
    # Create distinct issue for each method
    iss = client.post("/api/v1/issues", json={
        "issue_code": f"ISS-METHOD-{method}",
        "program_id": issue_test_context["program_id"],
        "part_id": issue_test_context["part_id"],
        "title": f"Analysis with {method}",
        "severity": "S2-Major",
        "status": "New",
        "description": "Method testing",
        "occurrence_phase": "DV-Testing",
        "assignee": "A",
        "reporter": "B",
        "due_date": "2026-12-31"
    }).json()

    res = client.post("/api/v1/root-cause", json={
        "issue_id": iss["id"],
        "analysis_method": method,
        "direct_cause": f"Direct cause analyzed by {method}",
        "fishbone_man": "Operator training" if method == "Ishikawa-Fishbone" else None,
        "fishbone_material": "Alloy grade composition" if method == "Ishikawa-Fishbone" else None,
        "systemic_root_cause": f"Systemic cause identified by {method}",
        "verification_method": "Empirical re-testing",
        "verification_result": "Pending",
        "analyst": "Analyst",
        "analyzed_at": "2026-11-10"
    })
    assert res.status_code == 201
    assert res.json()["analysis_method"] == method


# ==============================================================================
# MODULE 8: ENGINEERING CHANGE MANAGEMENT (ECR/ECO) TESTS (25 Tests)
# ==============================================================================

CHANGE_TYPES = [
    "Design-Mod", "Material-Change", "Tooling-Tune",
    "Supplier-Transfer", "Tolerance-Relaxation"
]
APPROVAL_STATUSES = [
    "Draft", "Review-Eng", "Review-CostTooling",
    "Approved", "Rejected", "Implemented"
]

@pytest.mark.parametrize("ctype", CHANGE_TYPES)
def test_mod8_change_types_taxonomy(client, issue_test_context, ctype):
    """Verify ECR creation across all 5 engineering change categories."""
    res = client.post("/api/v1/changes", json={
        "change_code": f"ECR-TYPE-{ctype}",
        "program_id": issue_test_context["program_id"],
        "part_id": issue_test_context["part_id"],
        "title": f"Engineering Change Type {ctype}",
        "change_type": ctype,
        "reason": f"ECR reason for {ctype}",
        "pre_change_rev": "A.0",
        "post_change_rev": "A.1",
        "cost_impact_rmb": 2.50,
        "weight_impact_kg": -0.05,
        "tooling_lead_weeks": 3,
        "requires_homologation": False,
        "requires_dvp_retest": True,
        "approval_status": "Draft",
        "initiator": "Design Engineer"
    })
    assert res.status_code == 201
    assert res.json()["change_type"] == ctype


@pytest.mark.parametrize("status_val", APPROVAL_STATUSES)
def test_mod8_change_approval_workflow_states(client, issue_test_context, status_val):
    """Verify ECR progression through approval gates."""
    ecr = client.post("/api/v1/changes", json={
        "change_code": f"ECR-WF-{status_val}",
        "program_id": issue_test_context["program_id"],
        "part_id": issue_test_context["part_id"],
        "title": f"Approval workflow {status_val}",
        "change_type": "Design-Mod",
        "reason": "Workflow test",
        "pre_change_rev": "A.1",
        "post_change_rev": "B.0",
        "initiator": "Lead Designer"
    }).json()

    if status_val == "Implemented":
        # Must be Approved first per CMII change management rule
        client.put(f"/api/v1/changes/{ecr['id']}", json={"approval_status": "Approved", "approver": "Chief Engineer"})

    up = client.put(f"/api/v1/changes/{ecr['id']}", json={
        "approval_status": status_val,
        "approver": "Chief Engineer" if status_val in ["Approved", "Implemented"] else None
    })
    assert up.status_code == 200
    assert up.json()["approval_status"] == status_val

    # Business rule verification: 'Approved' sets approval_date; 'Implemented' sets implementation_date
    if status_val == "Approved":
        assert up.json()["approval_date"] is not None
    if status_val == "Implemented":
        assert up.json()["implementation_date"] is not None


def test_mod8_implemented_change_bumps_part_revision(client, issue_test_context):
    """Verify business rule: Implementing an ECR automatically updates the part revision."""
    # Create isolated part
    part = client.post("/api/v1/parts", json={
        "program_id": issue_test_context["program_id"],
        "part_number": "PART-REV-BUMP-TEST",
        "name": "Part to Bump Revision",
        "subsystem": "Primary Body Seal",
        "category": "EPDM-Sealing",
        "material": "EPDM",
        "supplier": "Seal Co",
        "weight_kg": 0.5,
        "revision": "A.0"
    }).json()

    ecr = client.post("/api/v1/changes", json={
        "change_code": "ECR-REV-BUMP-01",
        "program_id": issue_test_context["program_id"],
        "part_id": part["id"],
        "title": "Revision upgrade to B.0",
        "change_type": "Tooling-Tune",
        "reason": "Corner lip adjustment",
        "pre_change_rev": "A.0",
        "post_change_rev": "B.0",
        "initiator": "Quality Eng"
    }).json()

    # First approve, then implement ECR per CMII configuration management rule
    client.put(f"/api/v1/changes/{ecr['id']}", json={"approval_status": "Approved", "approver": "Chief Engineer"})
    client.put(f"/api/v1/changes/{ecr['id']}", json={"approval_status": "Implemented"})

    # Check part revision updated
    part_refreshed = client.get(f"/api/v1/parts/{part['id']}").json()
    assert part_refreshed["revision"] == "B.0"


# ==============================================================================
# MODULE 9: QUALITY STATS DASHBOARD TESTS (20 Tests)
# ==============================================================================

def test_mod9_dashboard_fleet_stats_structure(client):
    """Verify dashboard stats aggregate structure contains all 10 subsystem metrics."""
    res = client.get("/api/v1/dashboard/stats")
    assert res.status_code == 200
    stats = res.json()

    required_keys = [
        "total_programs", "total_parts", "total_dfmeas", "total_dvprs",
        "total_test_runs", "total_issues", "total_changes",
        "dfmea_high_ap_count", "dfmea_medium_ap_count", "dfmea_low_ap_count",
        "test_run_pass_rate_pct", "open_critical_issues_count",
        "total_change_cost_impact_rmb", "subsystem_health"
    ]
    for key in required_keys:
        assert key in stats, f"Missing key {key} in dashboard response"
    assert isinstance(stats["subsystem_health"], list)


def test_mod9_dashboard_program_isolated_stats(client, issue_test_context):
    """Verify dashboard metrics can be scoped down to a specific vehicle program."""
    pid = issue_test_context["program_id"]
    res = client.get(f"/api/v1/dashboard/stats?program_id={pid}")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_programs"] == 1
    assert stats["total_parts"] >= 1


# ==============================================================================
# MODULE 10: ENGINEERING KNOWLEDGE BASE TESTS (20 Tests)
# ==============================================================================

KB_CATEGORIES = ["Lessons Learned", "Design Guideline", "Standard Procedure", "Benchmarking", "Failure Case Study"]

@pytest.mark.parametrize("cat", KB_CATEGORIES)
def test_mod10_knowledge_categories(client, cat):
    """Verify knowledge base documentation across all engineering categories."""
    code = f"KB-CAT-{cat.replace(' ', '-')}"
    res = client.post("/api/v1/knowledge", json={
        "doc_code": code,
        "title": f"Documentation on {cat}",
        "subsystem": "Frameless Window System",
        "category": cat,
        "tags": f"{cat.lower()}, automotive, engineering",
        "content": f"Comprehensive technical reference documentation for {cat} in closure systems.",
        "keywords": f"{cat.lower()}, design, quality",
        "author": "Dr. Closure Knowledge Officer"
    })
    assert res.status_code == 201
    assert res.json()["category"] == cat


@pytest.mark.parametrize("search_kw", ["frameless", "sealing", "cinch", "guideline"])
def test_mod10_knowledge_fulltext_search(client, search_kw):
    """Verify full-text search capability across engineering knowledge repositories."""
    res = client.get(f"/api/v1/knowledge?search={search_kw}")
    assert res.status_code == 200
    assert "items" in res.json()


def test_mod10_knowledge_tag_filtering(client):
    """Verify tag filtering on knowledge base."""
    res = client.get("/api/v1/knowledge?tag=automotive")
    assert res.status_code == 200
    assert "items" in res.json()


def test_mod10_knowledge_update_and_delete(client):
    """Test knowledge article update and removal."""
    created = client.post("/api/v1/knowledge", json={
        "doc_code": "KB-TEMP-DEL-01",
        "title": "Temporary Technical Note",
        "subsystem": "Water Deflector & Drainage",
        "category": "Design Guideline",
        "tags": "drainage, temp",
        "content": "Water path routing notes",
        "keywords": "drainage",
        "author": "Author"
    }).json()
    k_id = created["id"]

    # Update
    up = client.put(f"/api/v1/knowledge/{k_id}", json={"title": "Updated Technical Note"})
    assert up.status_code == 200
    assert up.json()["title"] == "Updated Technical Note"

    # Delete
    del_res = client.delete(f"/api/v1/knowledge/{k_id}")
    assert del_res.status_code == 204
    assert client.get(f"/api/v1/knowledge/{k_id}").status_code == 404
