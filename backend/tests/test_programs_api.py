def test_create_and_get_program(client):
    payload = {
        "code": "P-TEST01",
        "name": "Project Test EV",
        "platform": "EV-800V",
        "phase": "Proto-A",
        "sop_date": "2027-10-01",
        "lead_engineer": "Dr. Test",
        "quality_manager": "QA Leader",
        "target_market": "Global",
        "description": "Validation test vehicle"
    }
    res = client.post("/api/v1/programs", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["code"] == "P-TEST01"
    assert data["id"] is not None

    # Get by ID
    get_res = client.get(f"/api/v1/programs/{data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Project Test EV"

def test_program_duplicate_code(client):
    payload = {
        "code": "P-DUP01",
        "name": "Car 1",
        "platform": "Plat-A",
        "lead_engineer": "Eng 1",
        "quality_manager": "QM 1"
    }
    res1 = client.post("/api/v1/programs", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/programs", json=payload)
    assert res2.status_code == 409

def test_list_and_filter_programs(client):
    for i in range(5):
        client.post("/api/v1/programs", json={
            "code": f"P-LIST-{i}",
            "name": f"Car {i}",
            "platform": "EV" if i % 2 == 0 else "ICE",
            "phase": "Proto-A",
            "lead_engineer": f"Eng {i}",
            "quality_manager": "QM"
        })

    res = client.get("/api/v1/programs?platform=EV")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
