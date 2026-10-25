import pytest
from app.models.models import Program, Part, DFMEA, DVPR, TestRun, EngineeringIssue
TestRun.__test__ = False


# ==============================================================================
# SUITE 3: NUMERIC BOUNDARIES, VALIDATION & COMPLEX QUERIES (35 Tests)
# ==============================================================================

@pytest.fixture
def boundary_context(client):
    prog = client.post("/api/v1/programs", json={
        "code": "PROG-BOUNDARIES",
        "name": "Boundary Test Program",
        "platform": "P-BOUND",
        "phase": "DV",
        "lead_engineer": "Eng Lead",
        "quality_manager": "QM Lead",
        "target_market": "Domestic"
    }).json()

    part = client.post("/api/v1/parts", json={
        "program_id": prog["id"],
        "part_number": "PART-BOUND-01",
        "name": "Boundary Part",
        "subsystem": "Secondary Acoustic Weatherstrip",
        "category": "EPDM-Sealing",
        "material": "EPDM Sponge",
        "supplier": "SaarGummi",
        "weight_kg": 0.45,
        "revision": "A.0"
    }).json()

    return {"prog_id": prog["id"], "part_id": part["id"]}


@pytest.mark.parametrize("weight", [0.001, 0.5, 12.8, 45.0, 150.0])
def test_mod2_part_weight_boundaries(client, boundary_context, weight):
    """Verify part weights across ultra-light to heavy assemblies."""
    res = client.post("/api/v1/parts", json={
        "program_id": boundary_context["prog_id"],
        "part_number": f"PART-WT-{weight}",
        "name": f"Part weight {weight}kg",
        "subsystem": "Secondary Acoustic Weatherstrip",
        "category": "EPDM-Sealing",
        "material": "EPDM",
        "supplier": "SaarGummi",
        "weight_kg": weight,
        "revision": "A"
    })
    assert res.status_code == 201
    assert res.json()["weight_kg"] == weight


@pytest.mark.parametrize("sample_size", [1, 2, 5, 12, 30])
def test_mod4_dvpr_sample_sizes(client, boundary_context, sample_size):
    """Verify DVP&R sample sizes across prototype and statistical validation requirements."""
    res = client.post("/api/v1/dvpr", json={
        "program_id": boundary_context["prog_id"],
        "part_id": boundary_context["part_id"],
        "plan_code": f"DVP-SMP-{sample_size}",
        "test_phase": "DV-A",
        "test_name": f"Validation with sample size {sample_size}",
        "test_standard": "QC/T 627",
        "acceptance_criteria": "All samples pass",
        "sample_size": sample_size,
        "test_facility": "Facility A",
        "planned_start_date": "2026-11-01",
        "planned_end_date": "2026-11-15",
        "responsible_engineer": "Eng"
    })
    assert res.status_code == 201
    assert res.json()["sample_size"] == sample_size


@pytest.mark.parametrize("cycles", [100, 5000, 25000, 50000, 100000])
def test_mod5_testrun_durability_cycle_counts(client, boundary_context, cycles):
    """Verify test run telemetry records varying lifecycle durability cycle counts."""
    # Create DVPR
    dv = client.post("/api/v1/dvpr", json={
        "program_id": boundary_context["prog_id"],
        "part_id": boundary_context["part_id"],
        "plan_code": f"DVP-CYCLES-{cycles}",
        "test_phase": "PV-C",
        "test_name": f"Cycles {cycles}",
        "test_standard": "QC/T 627",
        "acceptance_criteria": "Pass",
        "sample_size": 2,
        "test_facility": "Lab",
        "planned_start_date": "2026-11-01",
        "planned_end_date": "2026-11-10",
        "responsible_engineer": "Eng"
    }).json()

    res = client.post("/api/v1/tests", json={
        "dvpr_id": dv["id"],
        "run_number": f"RUN-CYC-{cycles}",
        "sample_id": "SMP-01",
        "test_date": "2026-11-05",
        "test_facility": "Durability Rig",
        "operator": "Op Li",
        "temperature_c": 23.0,
        "humidity_rh": 50.0,
        "cycles_completed": cycles,
        "measurement_data": f'{{"target_cycles": {cycles}, "actual_cycles": {cycles}}}',
        "result": "Pass"
    })
    assert res.status_code == 201
    assert res.json()["cycles_completed"] == cycles


@pytest.mark.parametrize("cost", [0.0, 50.0, 1500.50, 25000.0, 120000.0])
def test_mod8_change_cost_impact_boundaries(client, boundary_context, cost):
    """Verify engineering change cost impact amounts from minor tune to major tooling rework."""
    res = client.post("/api/v1/changes", json={
        "change_code": f"ECR-COST-{int(cost)}",
        "program_id": boundary_context["prog_id"],
        "part_id": boundary_context["part_id"],
        "title": f"Change cost impact RMB {cost}",
        "change_type": "Tooling-Tune",
        "reason": "Cost boundary testing",
        "pre_change_rev": "A.0",
        "post_change_rev": "A.1",
        "cost_impact_rmb": cost,
        "weight_impact_kg": 0.0,
        "tooling_lead_weeks": 4,
        "initiator": "Cost Engineer"
    })
    assert res.status_code == 201
    assert res.json()["cost_impact_rmb"] == cost


@pytest.mark.parametrize("sev,stat", [
    ("S1-Critical", "New"),
    ("S1-Critical", "Investigating"),
    ("S2-Major", "Containment"),
    ("S2-Major", "RootCauseVerified"),
    ("S3-Minor", "ActionImplemented"),
    ("S3-Minor", "ValidationPass"),
    ("S4-Cosmetic", "Closed"),
])
def test_mod6_issue_multi_attribute_filtering(client, boundary_context, sev, stat):
    """Verify compound multi-attribute filtering (program AND severity AND status)."""
    # Seed issue
    client.post("/api/v1/issues", json={
        "issue_code": f"ISS-MULTI-{sev}-{stat}",
        "program_id": boundary_context["prog_id"],
        "part_id": boundary_context["part_id"],
        "title": f"Multi filter {sev} {stat}",
        "severity": sev,
        "status": stat,
        "description": "Multi filter test",
        "occurrence_phase": "DV-Testing",
        "assignee": "Eng",
        "reporter": "Tech",
        "due_date": "2026-12-31"
    })

    res = client.get(f"/api/v1/issues?program_id={boundary_context['prog_id']}&severity={sev}&status={stat}")
    assert res.status_code == 200
    for item in res.json()["items"]:
        assert item["severity"] == sev
        assert item["status"] == stat


def test_mod6_issue_empty_search_returns_all(client, boundary_context):
    """Verify empty search parameter returns normal paginated results."""
    res = client.get("/api/v1/issues?search=")
    assert res.status_code == 200
    assert "items" in res.json()


def test_mod6_issue_whitespace_title_rejected(client, boundary_context):
    """Verify issue creation with empty/whitespace-only required fields is rejected or trimmed."""
    res = client.post("/api/v1/issues", json={
        "issue_code": "ISS-WHITESPACE-REJECT",
        "program_id": boundary_context["prog_id"],
        "part_id": boundary_context["part_id"],
        "title": "",  # Empty title
        "severity": "S2-Major",
        "status": "New",
        "description": "Desc",
        "occurrence_phase": "DV-Testing",
        "assignee": "A",
        "reporter": "B",
        "due_date": "2026-12-31"
    })
    # Either 422 or handled
    assert res.status_code == 422


@pytest.mark.parametrize("market", ["China-Domestic", "EU-ECE", "US-FMVSS", "Global-Export"])
def test_mod1_program_target_market_taxonomy(client, market):
    """Verify vehicle programs targeting different automotive regulatory markets."""
    res = client.post("/api/v1/programs", json={
        "code": f"PROG-MKT-{market}",
        "name": f"Vehicle Model {market}",
        "platform": "E-PLATFORM",
        "phase": "DV",
        "lead_engineer": "Lead Eng",
        "quality_manager": "QM Lead",
        "target_market": market
    })
    assert res.status_code == 201
    assert res.json()["target_market"] == market


def test_traceability_nonexistent_issue_id(client):
    """Verify traceability endpoint returns 404 for invalid issue id."""
    res = client.get("/api/v1/traceability/lineage/999999")
    assert res.status_code == 404
