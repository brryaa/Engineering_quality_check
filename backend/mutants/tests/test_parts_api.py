def test_create_and_list_parts(client):
    # Create program first
    p_res = client.post("/api/v1/programs", json={
        "code": "P-PART-TEST",
        "name": "Part Test Platform",
        "platform": "EV-Modular",
        "phase": "Proto-A",
        "lead_engineer": "Lead",
        "quality_manager": "QM"
    })
    prog_id = p_res.json()["id"]

    # Create Part
    part_payload = {
        "program_id": prog_id,
        "part_number": "PT-SEAL-001",
        "name": "Front Door Primary Seal",
        "subsystem": "Primary Body Seal",
        "category": "Elastomer / Sealing",
        "supplier": "Cooper Standard",
        "material": "EPDM Sponge 45 Shore A",
        "revision": "Rev A.0",
        "weight_kg": 1.25,
        "safety_critical": False
    }
    res = client.post("/api/v1/parts", json=part_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["part_number"] == "PT-SEAL-001"
    assert data["program_code"] == "P-PART-TEST"

    # List with subsystem filter
    list_res = client.get(f"/api/v1/parts?subsystem=Primary Body Seal")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

def test_part_invalid_program(client):
    res = client.post("/api/v1/parts", json={
        "program_id": 99999,
        "part_number": "PT-ERR-001",
        "name": "Invalid",
        "subsystem": "Front Door Closure",
        "category": "Mechanical",
        "supplier": "Brose",
        "material": "Steel",
        "revision": "Rev A.0",
        "weight_kg": 2.0
    })
    assert res.status_code == 400
