def test_create_and_filter_dvpr(client):
    # Setup program and part
    p = client.post("/api/v1/programs", json={
        "code": "P-DVP-TEST", "name": "DVP Car", "platform": "EV", "lead_engineer": "Eng", "quality_manager": "QM"
    }).json()
    pt = client.post("/api/v1/parts", json={
        "program_id": p["id"], "part_number": "PT-DVP-01", "name": "Weatherstrip Primary",
        "subsystem": "Primary Body Seal", "category": "Elastomer", "supplier": "Cooper", "material": "EPDM"
    }).json()

    dvp_payload = {
        "program_id": p["id"],
        "part_id": pt["id"],
        "plan_code": "DVP-2026-T1",
        "test_phase": "DV-A",
        "test_name": "High Pressure Water Leakage",
        "test_standard": "ISO 20653 IPX9K",
        "acceptance_criteria": "Zero water entry into cabin",
        "sample_size": 3,
        "test_facility": "Rain Chamber 3",
        "planned_start_date": "2026-11-01",
        "planned_end_date": "2026-11-15",
        "status": "Planned",
        "responsible_engineer": "Eng"
    }
    res = client.post("/api/v1/dvpr", json=dvp_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["plan_code"] == "DVP-2026-T1"
    assert data["program_code"] == "P-DVP-TEST"
    assert data["part_number"] == "PT-DVP-01"

    # Filter by test_phase
    list_res = client.get("/api/v1/dvpr?test_phase=DV-A")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
