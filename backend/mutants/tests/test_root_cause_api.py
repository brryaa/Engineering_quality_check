def test_create_and_verify_root_cause(client):
    # Setup program, part, and issue
    p = client.post("/api/v1/programs", json={
        "code": "P-RC-P", "name": "RC Program", "platform": "EV", "lead_engineer": "Eng", "quality_manager": "QM"
    }).json()
    pt = client.post("/api/v1/parts", json={
        "program_id": p["id"], "part_number": "PT-RC-01", "name": "Cinch Motor Latch",
        "subsystem": "Tailgate Spindle & Cinch Latch", "category": "Electro-Mechanical", "supplier": "Kiekert", "material": "POM"
    }).json()
    issue = client.post("/api/v1/issues", json={
        "issue_code": "ISS-RC-001",
        "program_id": p["id"],
        "part_id": pt["id"],
        "title": "Cinch motor gear tooth fracture under shock slam",
        "severity": "S2-Major",
        "status": "Investigating",
        "description": "Gear tooth chipped after 20,000 slam cycles",
        "occurrence_phase": "DV-Testing",
        "assignee": "Liang Zhang",
        "reporter": "Tester B",
        "due_date": "2026-11-20"
    }).json()

    # Create 5-Why root cause analysis with Confirmed result
    rc_payload = {
        "issue_id": issue["id"],
        "analysis_method": "5-Why",
        "direct_cause": "Gear tooth root bending fatigue fracture",
        "why_1": "Gear tooth broke under impact load",
        "why_2": "Impact load exceeded tooth root yield strength",
        "why_3": "Root fillet radius was 0.3mm instead of 0.8mm",
        "why_4": "Injection mold tooling EDM electrode was undersized",
        "why_5": "Tooling drawing lacked explicit fillet radius tolerance note",
        "systemic_root_cause": "Tooling release standard checklist did not mandate micro-geometry inspection",
        "fishbone_machine": "EDM wire cutter electrode radius wear",
        "verification_method": "Sample gear with R0.8mm fillet tested for 50,000 cycles with zero fracture",
        "verification_result": "Confirmed",
        "analyst": "Liang Zhang",
        "analyzed_at": "2026-11-10"
    }
    res = client.post("/api/v1/root-cause", json=rc_payload)
    assert res.status_code == 201
    rc_data = res.json()
    assert rc_data["issue_code"] == "ISS-RC-001"
    assert rc_data["verification_result"] == "Confirmed"

    # Verify that issue status was automatically promoted to RootCauseVerified
    issue_updated = client.get(f"/api/v1/issues/{issue['id']}").json()
    assert issue_updated["status"] == "RootCauseVerified"
    assert issue_updated["has_root_cause"] is True
