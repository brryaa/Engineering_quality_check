def test_create_issue_and_closure_lifecycle(client):
    p = client.post("/api/v1/programs", json={
        "code": "P-ISS-P", "name": "Issue Car", "platform": "EV", "lead_engineer": "Eng", "quality_manager": "QM"
    }).json()
    pt = client.post("/api/v1/parts", json={
        "program_id": p["id"], "part_number": "PT-ISS-01", "name": "A-Pillar Seal",
        "subsystem": "Primary Body Seal", "category": "Elastomer", "supplier": "Cooper", "material": "EPDM"
    }).json()

    issue_payload = {
        "issue_code": "ISS-TEST-001",
        "program_id": p["id"],
        "part_id": pt["id"],
        "title": "Water leak past A-pillar seal during storm rain test",
        "severity": "S1-Critical",
        "status": "New",
        "description": "Cabin driver side A-pillar drip observed",
        "occurrence_phase": "DV-Testing",
        "containment_action": "Add temporary deflector tape on pilot vehicles",
        "assignee": "Dr. Wei Chen",
        "reporter": "Tester A",
        "due_date": "2026-11-30"
    }
    res = client.post("/api/v1/issues", json=issue_payload)
    assert res.status_code == 201
    issue_data = res.json()
    assert issue_data["severity"] == "S1-Critical"
    assert issue_data["closure_date"] is None

    # Transition to Closed without closure_date -> should auto-fill closure date
    close_res = client.put(f"/api/v1/issues/{issue_data['id']}", json={"status": "Closed"})
    assert close_res.status_code == 200
    closed_data = close_res.json()
    assert closed_data["status"] == "Closed"
    assert closed_data["closure_date"] is not None
