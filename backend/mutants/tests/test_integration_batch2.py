def test_tri_module_integration_dvpr_testrun_issues(client):
    # 1. Create Program & Part
    p = client.post("/api/v1/programs", json={
        "code": "P-INTEG-B2", "name": "B2 Platform", "platform": "EV-Pure", "lead_engineer": "Eng", "quality_manager": "QM"
    }).json()
    pt = client.post("/api/v1/parts", json={
        "program_id": p["id"], "part_number": "PT-B2-01", "name": "Glass Regulator Motor",
        "subsystem": "Frameless Window System", "category": "Electro-Mechanical", "supplier": "Brose", "material": "POM/Cu"
    }).json()

    # 2. Create DVP plan for anti-pinch test
    dvp = client.post("/api/v1/dvpr", json={
        "program_id": p["id"],
        "part_id": pt["id"],
        "plan_code": "DVP-B2-PINCH",
        "test_phase": "DV-B",
        "test_name": "Window Anti-Pinch Cold Verification",
        "test_standard": "ECE R21",
        "acceptance_criteria": "Pinch force < 100N at -40C",
        "sample_size": 3,
        "test_facility": "Environmental Chamber 2",
        "planned_start_date": "2026-11-01",
        "planned_end_date": "2026-11-20",
        "status": "In Progress",
        "responsible_engineer": "Marcus Lindholm"
    }).json()

    # 3. Execute cold test run where it fails with pinch force = 125N > 100N
    tr = client.post("/api/v1/tests", json={
        "dvpr_id": dvp["id"],
        "run_number": "RUN-B2-PINCH-01",
        "sample_id": "SMP-PINCH-01",
        "test_date": "2026-11-05",
        "test_facility": "Environmental Chamber 2",
        "operator": "Marcus Lindholm",
        "temperature_c": -40.0,
        "humidity_rh": 40.0,
        "cycles_completed": 1200,
        "measurement_data": '{"pinch_force_n": 125.4, "motor_current_a": 18.2}',
        "result": "Fail",
        "failure_summary": "Pinch force 125.4N exceeded 100N regulatory threshold under -40C soak."
    }).json()

    # 4. Create an Engineering Issue directly linked to this failed test run
    issue = client.post("/api/v1/issues", json={
        "issue_code": "ISS-B2-PINCH-01",
        "program_id": p["id"],
        "part_id": pt["id"],
        "test_run_id": tr["id"],
        "title": "Anti-pinch regulatory non-compliance at -40°C",
        "severity": "S1-Critical",
        "status": "Investigating",
        "description": tr["failure_summary"],
        "occurrence_phase": "DV-Testing",
        "containment_action": "Freeze software release SW04.2; limit regulator low-temperature duty cycle",
        "assignee": "Marcus Lindholm",
        "reporter": "Marcus Lindholm",
        "due_date": "2026-11-25"
    }).json()

    assert issue["test_run_id"] == tr["id"]
    assert issue["severity"] == "S1-Critical"

    # 5. Query issue list filtered by severity and verify linkage
    list_issues_res = client.get(f"/api/v1/issues?program_id={p['id']}&severity=S1-Critical")
    assert list_issues_res.status_code == 200
    res_items = list_issues_res.json()["items"]
    assert len(res_items) == 1
    assert res_items[0]["issue_code"] == "ISS-B2-PINCH-01"
    assert res_items[0]["part_number"] == "PT-B2-01"
