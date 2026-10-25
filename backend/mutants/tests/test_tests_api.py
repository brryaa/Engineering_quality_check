def test_create_test_run_and_sync_status(client):
    p = client.post("/api/v1/programs", json={
        "code": "P-TR-P", "name": "TR Program", "platform": "EV", "lead_engineer": "Eng", "quality_manager": "QM"
    }).json()
    pt = client.post("/api/v1/parts", json={
        "program_id": p["id"], "part_number": "PT-TR-01", "name": "Door Latch",
        "subsystem": "Front Door Closure", "category": "Mechanical", "supplier": "Kiekert", "material": "Steel"
    }).json()
    dvp = client.post("/api/v1/dvpr", json={
        "program_id": p["id"], "part_id": pt["id"], "plan_code": "DVP-TR-01",
        "test_phase": "DV-A", "test_name": "Door Slam 100k Cycles", "test_standard": "QC/T 627",
        "acceptance_criteria": "Door sag < 1.5mm", "sample_size": 2, "test_facility": "Rig 1",
        "planned_start_date": "2026-10-01", "planned_end_date": "2026-10-20", "status": "Planned",
        "responsible_engineer": "Eng"
    }).json()

    # Create failing test run
    tr_payload = {
        "dvpr_id": dvp["id"],
        "run_number": "RUN-TR-001",
        "sample_id": "SMP-001",
        "test_date": "2026-10-15",
        "test_facility": "Rig 1",
        "operator": "Frank Becker",
        "temperature_c": 23.0,
        "humidity_rh": 50.0,
        "cycles_completed": 75000,
        "measurement_data": '{"residual_sag_mm": 2.2}',
        "result": "Fail",
        "failure_summary": "Door sag reached 2.2mm at cycle 75k."
    }
    res = client.post("/api/v1/tests", json=tr_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["result"] == "Fail"

    # Verify DVP status synced to "Failed"
    dvp_check = client.get(f"/api/v1/dvpr/{dvp['id']}").json()
    assert dvp_check["status"] == "Failed"
    assert dvp_check["test_runs_count"] == 1
