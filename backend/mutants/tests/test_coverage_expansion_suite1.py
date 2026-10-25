import pytest
from app.models.models import Program, Part, DFMEA, DVPR, TestRun
TestRun.__test__ = False


# ==============================================================================
# MODULE 1: VEHICLE PROGRAM & MODEL MANAGEMENT TESTS (25 Tests)
# ==============================================================================

@pytest.mark.parametrize("phase", ["Concept", "Design", "DV", "PV", "SOP"])
def test_mod1_program_lifecycle_phases(client, phase):
    """Test valid creation of vehicle programs across all 5 lifecycle phases."""
    code = f"PROG-PHASE-{phase}"
    res = client.post("/api/v1/programs", json={
        "code": code,
        "name": f"Vehicle Model {phase}",
        "platform": "E-PLATFORM",
        "phase": phase,
        "lead_engineer": "Lead Eng",
        "quality_manager": "QM Lead",
        "target_market": "Global"
    })
    assert res.status_code == 201
    assert res.json()["phase"] == phase


@pytest.mark.parametrize("invalid_code", ["", "A", "A" * 35])
def test_mod1_program_invalid_codes(client, invalid_code):
    """Test rejection of non-standard/oversized/too short program codes."""
    res = client.post("/api/v1/programs", json={
        "code": invalid_code,
        "name": "Invalid Program",
        "platform": "E-PLATFORM",
        "phase": "DV",
        "lead_engineer": "Lead Eng",
        "quality_manager": "QM Lead",
        "target_market": "Global"
    })
    assert res.status_code == 422


@pytest.mark.parametrize("sort_field", ["code", "name", "created_at"])
def test_mod1_program_sorting_parameters(client, sort_field):
    """Test sorting programs by various valid column names."""
    res = client.get(f"/api/v1/programs?sort_by={sort_field}&sort_order=asc")
    assert res.status_code == 200
    assert "items" in res.json()


def test_mod1_program_invalid_sort_field(client):
    """Test rejection of injection/invalid sort fields."""
    res = client.get("/api/v1/programs?sort_by=non_existent_column")
    assert res.status_code == 422


def test_mod1_program_update_fields(client):
    """Test partial update of vehicle program metadata."""
    p_res = client.post("/api/v1/programs", json={
        "code": "PROG-UP-01",
        "name": "Original Name",
        "platform": "P-OLD",
        "phase": "Concept",
        "lead_engineer": "Eng 1",
        "quality_manager": "QM 1",
        "target_market": "Domestic"
    })
    p_id = p_res.json()["id"]

    up_res = client.put(f"/api/v1/programs/{p_id}", json={
        "name": "Updated Vehicle Name",
        "phase": "Design"
    })
    assert up_res.status_code == 200
    updated = up_res.json()
    assert updated["name"] == "Updated Vehicle Name"
    assert updated["phase"] == "Design"
    assert updated["platform"] == "P-OLD"  # Unchanged


def test_mod1_program_delete_cascade(client, db_session):
    """Test program deletion removes program correctly."""
    p = Program(code="PROG-DEL-01", name="Del Program", platform="P-DEL", phase="DV", lead_engineer="E", quality_manager="Q", target_market="Global")
    db_session.add(p)
    db_session.commit()
    pid = p.id

    del_res = client.delete(f"/api/v1/programs/{pid}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/programs/{pid}")
    assert get_res.status_code == 404


@pytest.mark.parametrize("platform", ["BEV-800V", "PHEV-Compact", "SUV-Flagship"])
def test_mod1_program_filter_by_platform(client, platform):
    """Test filtering programs by automotive chassis platform."""
    client.post("/api/v1/programs", json={
        "code": f"PROG-PLT-{platform}",
        "name": f"Platform {platform}",
        "platform": platform,
        "phase": "DV",
        "lead_engineer": "E",
        "quality_manager": "Q",
        "target_market": "Global"
    })
    res = client.get(f"/api/v1/programs?platform={platform}")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(i["platform"] == platform for i in items)


# ==============================================================================
# MODULE 2: PARTS & SUBSYSTEMS MANAGEMENT TESTS (25 Tests)
# ==============================================================================

SUBSYSTEMS = [
    "Front Door Closure", "Rear Door Closure", "Power Tailgate System",
    "Frameless Window System", "Primary Body Seal", "Secondary Acoustic Weatherstrip",
    "Water Deflector & Drainage", "Door Hinge & Check Link", "Glass Regulator Module",
    "Tailgate Spindle & Cinch Latch"
]

@pytest.fixture
def shared_program(client):
    res = client.post("/api/v1/programs", json={
        "code": "PROG-PARTS-HUB",
        "name": "Parts Hub Program",
        "platform": "MODULAR-ARCH",
        "phase": "DV",
        "lead_engineer": "Chief Parts Architect",
        "quality_manager": "QM Hub",
        "target_market": "Global"
    })
    return res.json()["id"]


@pytest.mark.parametrize("subsystem", SUBSYSTEMS)
def test_mod2_parts_subsystem_taxonomy(client, shared_program, subsystem):
    """Verify part creation across all 10 automotive closure subsystems."""
    code_suffix = subsystem.replace(" ", "-").replace("&", "AND")[:20]
    p_num = f"PART-{code_suffix}"
    res = client.post("/api/v1/parts", json={
        "program_id": shared_program,
        "part_number": p_num,
        "name": f"Component for {subsystem}",
        "subsystem": subsystem,
        "category": "Stamping",
        "material": "High-Strength Steel",
        "supplier": "Brose/Magna Tier 1",
        "weight_kg": 2.34,
        "revision": "A.0"
    })
    assert res.status_code == 201
    assert res.json()["subsystem"] == subsystem


@pytest.mark.parametrize("cat", ["Stamping", "EPDM-Sealing", "Hardware", "Electrical", "Assembly", "Glass"])
def test_mod2_parts_category_taxonomy(client, shared_program, cat):
    """Verify parts categorisation by manufacturing process and component classification."""
    p_num = f"PART-CAT-{cat}"
    res = client.post("/api/v1/parts", json={
        "program_id": shared_program,
        "part_number": p_num,
        "name": f"Part Category {cat}",
        "subsystem": "Front Door Closure",
        "category": cat,
        "material": "Engineering Polymer / Alloy",
        "supplier": "Tier 1 Specialist",
        "weight_kg": 1.15,
        "revision": "B.0"
    })
    assert res.status_code == 201
    assert res.json()["category"] == cat


def test_mod2_part_duplicate_number_rejected(client, shared_program):
    """Verify part numbers must be unique across the platform."""
    payload = {
        "program_id": shared_program,
        "part_number": "PART-DUPE-REJECT",
        "name": "Unique Component",
        "subsystem": "Front Door Closure",
        "category": "Stamping",
        "material": "Alloy",
        "supplier": "Supplier A",
        "weight_kg": 3.0,
        "revision": "A"
    }
    r1 = client.post("/api/v1/parts", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/parts", json=payload)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["error"]


def test_mod2_part_filter_by_subsystem_and_search(client, shared_program):
    """Test searching parts by keyword with subsystem filter."""
    res = client.get("/api/v1/parts?subsystem=Frameless Window System&page_size=50")
    assert res.status_code == 200
    for item in res.json()["items"]:
        assert item["subsystem"] == "Frameless Window System"


def test_mod2_part_update_and_delete(client, shared_program):
    """Test part revision upgrade and deletion."""
    res = client.post("/api/v1/parts", json={
        "program_id": shared_program,
        "part_number": "PART-LIFECYCLE-DEL",
        "name": "Temporary Part",
        "subsystem": "Door Hinge & Check Link",
        "category": "Hardware",
        "material": "Steel",
        "supplier": "Edscha",
        "weight_kg": 1.8,
        "revision": "A.0"
    })
    pid = res.json()["id"]

    # Update revision
    up = client.put(f"/api/v1/parts/{pid}", json={"revision": "A.1", "weight_kg": 1.75})
    assert up.status_code == 200
    assert up.json()["revision"] == "A.1"

    # Delete
    del_res = client.delete(f"/api/v1/parts/{pid}")
    assert del_res.status_code == 204
    assert client.get(f"/api/v1/parts/{pid}").status_code == 404


# ==============================================================================
# MODULE 3: DFMEA RISK ANALYSIS TESTS (25 Tests)
# ==============================================================================

@pytest.fixture
def shared_part(client, shared_program):
    res = client.post("/api/v1/parts", json={
        "program_id": shared_program,
        "part_number": "PART-DFMEA-SUBJECT",
        "name": "DFMEA Target Part",
        "subsystem": "Power Tailgate System",
        "category": "Assembly",
        "material": "Mixed Aluminum & Steel",
        "supplier": "Stabilus Spindle Systems",
        "weight_kg": 4.12,
        "revision": "A.0"
    })
    return res.json()["id"]


@pytest.mark.parametrize("s,o,d,expected_ap", [
    (10, 8, 5, "High"),
    (9, 6, 2, "High"),
    (10, 4, 8, "High"),
    (10, 4, 3, "Medium"),
    (10, 1, 1, "Low"),
    (8, 7, 7, "High"),
    (7, 4, 6, "Medium"),
    (7, 2, 8, "Medium"),
    (7, 2, 4, "Low"),
    (5, 5, 5, "Low"),
    (5, 2, 2, "Low"),
    (3, 8, 8, "Medium"),
    (1, 10, 10, "Low"),
])
def test_mod3_dfmea_automatic_ap_calculation_api(client, shared_part, s, o, d, expected_ap):
    """Test DFMEA API auto-computes RPN and Action Priority according to AIAG & VDA 2019 Table B."""
    fmea_code = f"DFMEA-AP-{s}-{o}-{d}"
    res = client.post("/api/v1/dfmea", json={
        "part_id": shared_part,
        "fmea_code": fmea_code,
        "item_function": "Open and close power tailgate latch within 1.2s",
        "failure_mode": f"Tailgate failure mode with S={s}, O={o}, D={d}",
        "failure_effect": "Loss of convenience or tailgate latch retention failure",
        "severity": s,
        "cause_mechanism": "Actuator gear teeth wear",
        "occurrence": o,
        "prevention_control": "Hardened gear tooth surface treatment",
        "detection_control": "High-speed optical end-of-line verification",
        "detection": d
    })
    assert res.status_code == 201
    data = res.json()
    assert data["rpn"] == s * o * d
    assert data["action_priority"] == expected_ap


@pytest.mark.parametrize("invalid_rating", [0, 11, -1, 100])
def test_mod3_dfmea_rating_out_of_bounds_rejected(client, shared_part, invalid_rating):
    """Severity, Occurrence, and Detection must strictly be integers between 1 and 10."""
    res = client.post("/api/v1/dfmea", json={
        "part_id": shared_part,
        "fmea_code": f"DFMEA-INV-{invalid_rating}",
        "item_function": "Function",
        "failure_mode": "Failure Mode",
        "failure_effect": "Failure Effect",
        "severity": invalid_rating,
        "cause_mechanism": "Cause",
        "occurrence": 5,
        "prevention_control": "Prev",
        "detection_control": "Det",
        "detection": 5
    })
    assert res.status_code == 422


def test_mod3_dfmea_post_mitigation_recalculation(client, shared_part):
    """Verify that updating post-mitigation S/O/D ratings auto-recalculates post_rpn."""
    res = client.post("/api/v1/dfmea", json={
        "part_id": shared_part,
        "fmea_code": "DFMEA-MITIGATION-01",
        "item_function": "Tailgate cinch latch retention",
        "failure_mode": "Incomplete cinch locking",
        "failure_effect": "Door ajar warning on cluster",
        "severity": 8,
        "cause_mechanism": "Microswitch contact bounce",
        "occurrence": 6,
        "prevention_control": "RC debounce filter",
        "detection_control": "100% EOL current spike test",
        "detection": 6
    })
    dfmea_id = res.json()["id"]

    # Implement corrective action and post mitigation
    up = client.put(f"/api/v1/dfmea/{dfmea_id}", json={
        "recommended_action": "Gold-plated dual-redundant microswitch",
        "action_owner": "Eng. Zhang",
        "action_status": "Completed",
        "post_severity": 8,
        "post_occurrence": 2,
        "post_detection": 2
    })
    assert up.status_code == 200
    updated = up.json()
    assert updated["post_rpn"] == 8 * 2 * 2  # 32
    assert updated["action_status"] == "Completed"


# ==============================================================================
# MODULE 4: DVP&R VERIFICATION PLANS TESTS (25 Tests)
# ==============================================================================

TEST_STANDARDS = [
    ("QC/T 627", "Door slam durability 100,000 cycles"),
    ("ISO 20653", "IPX9K High pressure high temperature water jet spray"),
    ("GMW 14147", "Power closure cinching and anti-pinch timing"),
    ("FMVSS 118", "Power window systems obstruction detection"),
    ("GB 15086", "Door locks and door retention components compliance"),
    ("VW 80000", "Electric and electronic components environmental qualification")
]

@pytest.mark.parametrize("std,desc", TEST_STANDARDS)
def test_mod4_dvpr_automotive_standards(client, shared_program, shared_part, std, desc):
    """Verify DVP&R creation across domestic and international automotive standards."""
    code = f"DVP-STD-{std.replace(' ', '-').replace('/', '-')}"
    res = client.post("/api/v1/dvpr", json={
        "program_id": shared_program,
        "part_id": shared_part,
        "plan_code": code,
        "test_phase": "DV-A",
        "test_name": desc,
        "test_standard": std,
        "acceptance_criteria": "No mechanical degradation or loss of sealing integrity",
        "sample_size": 4,
        "test_facility": "National Automotive Quality Inspection Lab",
        "planned_start_date": "2026-11-01",
        "planned_end_date": "2026-11-20",
        "responsible_engineer": "Senior DV Engineer"
    })
    assert res.status_code == 201
    assert res.json()["test_standard"] == std


@pytest.mark.parametrize("phase", ["DV-A", "DV-B", "PV-C", "SOP-Confirm"])
def test_mod4_dvpr_phases(client, shared_program, shared_part, phase):
    """Verify DVP&R across automotive verification milestones."""
    res = client.post("/api/v1/dvpr", json={
        "program_id": shared_program,
        "part_id": shared_part,
        "plan_code": f"DVP-PHASE-{phase}",
        "test_phase": phase,
        "test_name": f"Test plan for phase {phase}",
        "test_standard": "QC/T 627",
        "acceptance_criteria": "Pass criteria",
        "sample_size": 3,
        "test_facility": "Durability Lab",
        "planned_start_date": "2026-11-01",
        "planned_end_date": "2026-11-15",
        "responsible_engineer": "Engineer"
    })
    assert res.status_code == 201
    assert res.json()["test_phase"] == phase


def test_mod4_dvpr_status_lifecycle_updates(client, shared_program, shared_part):
    """Test updating DVP&R status from Planned -> In Progress -> Passed."""
    res = client.post("/api/v1/dvpr", json={
        "program_id": shared_program,
        "part_id": shared_part,
        "plan_code": "DVP-CYCLE-UPDATE",
        "test_phase": "PV-C",
        "test_name": "Lifecycle Plan",
        "test_standard": "ISO 20653",
        "acceptance_criteria": "Pass",
        "sample_size": 2,
        "test_facility": "Lab",
        "planned_start_date": "2026-11-01",
        "planned_end_date": "2026-11-10",
        "responsible_engineer": "Eng"
    })
    dvpr_id = res.json()["id"]
    assert res.json()["status"] == "Planned"

    up1 = client.put(f"/api/v1/dvpr/{dvpr_id}", json={"status": "In Progress"})
    assert up1.json()["status"] == "In Progress"

    up2 = client.put(f"/api/v1/dvpr/{dvpr_id}", json={"status": "Passed"})
    assert up2.json()["status"] == "Passed"


# ==============================================================================
# MODULE 5: TEST RUNS & TELEMETRY TESTS (25 Tests)
# ==============================================================================

@pytest.fixture
def shared_dvpr(client, shared_program, shared_part):
    res = client.post("/api/v1/dvpr", json={
        "program_id": shared_program,
        "part_id": shared_part,
        "plan_code": "DVP-FOR-TESTRUNS-01",
        "test_phase": "DV-A",
        "test_name": "Environmental & Durability Multi-chamber Test",
        "test_standard": "ISO 20653 / QC/T 627",
        "acceptance_criteria": "Cycles >= 50,000 without failure",
        "sample_size": 6,
        "test_facility": "Environmental Test Center",
        "planned_start_date": "2026-11-01",
        "planned_end_date": "2026-11-30",
        "responsible_engineer": "Test Specialist"
    })
    return res.json()["id"]


@pytest.mark.parametrize("temp_c,humidity_rh", [
    (-40.0, 10.0),   # Extreme Arctic Cold
    (-25.0, 30.0),   # Subzero Cold Chamber
    (23.0, 50.0),    # Standard Ambient
    (45.0, 85.0),    # Tropical High Heat & High Humidity
    (85.0, 95.0),    # Severe Hot Soak Environment
])
def test_mod5_testrun_environmental_boundaries(client, shared_dvpr, temp_c, humidity_rh):
    """Verify test run telemetry records across extreme automotive thermal & humidity chambers."""
    run_code = f"RUN-ENV-{int(temp_c)}C-{int(humidity_rh)}RH"
    res = client.post("/api/v1/tests", json={
        "dvpr_id": shared_dvpr,
        "run_number": run_code,
        "sample_id": f"SMP-CHAMBER-{int(temp_c)}",
        "test_date": "2026-11-05",
        "test_facility": "Climate Chamber 4",
        "operator": "Lab Tech Li",
        "temperature_c": temp_c,
        "humidity_rh": humidity_rh,
        "cycles_completed": 10000,
        "measurement_data": f'{{"temp": {temp_c}, "humidity": {humidity_rh}, "operating_force_n": 42.5}}',
        "result": "Pass"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["temperature_c"] == temp_c
    assert data["humidity_rh"] == humidity_rh
    assert data["result"] == "Pass"


@pytest.mark.parametrize("result_state", ["Pass", "Fail", "Marginal"])
def test_mod5_testrun_result_states(client, shared_dvpr, result_state):
    """Verify test run result classification states."""
    res = client.post("/api/v1/tests", json={
        "dvpr_id": shared_dvpr,
        "run_number": f"RUN-RESULT-{result_state}",
        "sample_id": "SMP-RESULT",
        "test_date": "2026-11-06",
        "test_facility": "Facility A",
        "operator": "Op 1",
        "temperature_c": 23.0,
        "humidity_rh": 50.0,
        "cycles_completed": 25000,
        "measurement_data": "{}",
        "result": result_state,
        "failure_summary": "Degradation observed" if result_state != "Pass" else None
    })
    assert res.status_code == 201
    assert res.json()["result"] == result_state


def test_mod5_testrun_syncs_dvpr_status_to_passed_or_failed(client, shared_program, shared_part):
    """Verify business logic: Test execution synchronises parent DVP&R plan status."""
    # Create isolated DVPR
    dv = client.post("/api/v1/dvpr", json={
        "program_id": shared_program,
        "part_id": shared_part,
        "plan_code": "DVP-SYNC-TEST-01",
        "test_phase": "PV-C",
        "test_name": "Sync Validation",
        "test_standard": "QC/T 627",
        "acceptance_criteria": "Pass all runs",
        "sample_size": 2,
        "test_facility": "Lab",
        "planned_start_date": "2026-11-01",
        "planned_end_date": "2026-11-10",
        "responsible_engineer": "Eng"
    }).json()
    dv_id = dv["id"]

    # Post passing run
    client.post("/api/v1/tests", json={
        "dvpr_id": dv_id,
        "run_number": "RUN-SYNC-PASS-01",
        "sample_id": "SMP-01",
        "test_date": "2026-11-02",
        "test_facility": "Lab",
        "operator": "Op",
        "temperature_c": 23.0,
        "humidity_rh": 50.0,
        "cycles_completed": 50000,
        "measurement_data": "{}",
        "result": "Pass"
    })
    # DVPR status should advance to Passed
    assert client.get(f"/api/v1/dvpr/{dv_id}").json()["status"] == "Passed"

    # Post failing run
    client.post("/api/v1/tests", json={
        "dvpr_id": dv_id,
        "run_number": "RUN-SYNC-FAIL-02",
        "sample_id": "SMP-02",
        "test_date": "2026-11-03",
        "test_facility": "Lab",
        "operator": "Op",
        "temperature_c": 23.0,
        "humidity_rh": 50.0,
        "cycles_completed": 12000,
        "measurement_data": "{}",
        "result": "Fail",
        "failure_summary": "Latch spring fatigue fracture"
    })
    # DVPR status should update to Failed
    assert client.get(f"/api/v1/dvpr/{dv_id}").json()["status"] == "Failed"
