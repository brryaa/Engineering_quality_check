def test_tri_module_integration_programs_parts_dfmea(client):
    # 1. Create Program
    p_res = client.post("/api/v1/programs", json={
        "code": "P-INTEG-B1",
        "name": "Integration Program 1",
        "platform": "EV-800V",
        "phase": "Proto-A",
        "lead_engineer": "Chief Chen",
        "quality_manager": "QA Director"
    })
    assert p_res.status_code == 201
    prog_id = p_res.json()["id"]

    # 2. Create multiple Parts for this Program
    parts_created = []
    for i in range(3):
        pt_res = client.post("/api/v1/parts", json={
            "program_id": prog_id,
            "part_number": f"PT-B1-00{i}",
            "name": f"Part Door Component {i}",
            "subsystem": "Front Door Closure",
            "category": "Mechanical",
            "supplier": "Brose",
            "material": "Steel DP600",
            "revision": "Rev A.0",
            "weight_kg": 2.5 + i
        })
        assert pt_res.status_code == 201
        parts_created.append(pt_res.json())

    # 3. Create DFMEA entries for the parts
    fmea_ids = []
    for i, pt in enumerate(parts_created):
        fmea_res = client.post("/api/v1/dfmea", json={
            "part_id": pt["id"],
            "fmea_code": f"DFMEA-B1-{i}",
            "item_function": "Structural door slamming retention",
            "failure_mode": f"Hinge bush excessive deformation under fatigue cycle {i}",
            "failure_effect": "Door sag > 1.8mm, latch misalignment",
            "severity": 8,
            "cause_mechanism": "Bush thickness inadequate",
            "occurrence": 7 - i,
            "prevention_control": "CAD thickness specification",
            "detection_control": "Durability test 100k cycles",
            "detection": 4
        })
        assert fmea_res.status_code == 201
        fmea_ids.append(fmea_res.json()["id"])

    # 4. Verify listing DFMEA sorted by RPN desc
    list_dfmea_res = client.get("/api/v1/dfmea?sort_by=rpn&sort_order=desc")
    assert list_dfmea_res.status_code == 200
    items = list_dfmea_res.json()["items"]
    assert len(items) == 3
    # Check descending order
    rpns = [item["rpn"] for item in items]
    assert rpns == sorted(rpns, reverse=True)

    # 5. Verify Program deletion cascade deletes parts and dfmeas
    del_res = client.delete(f"/api/v1/programs/{prog_id}")
    assert del_res.status_code == 204

    # Parts should be gone
    get_part_res = client.get(f"/api/v1/parts/{parts_created[0]['id']}")
    assert get_part_res.status_code == 404

    # DFMEAs should be gone
    get_fmea_res = client.get(f"/api/v1/dfmea/{fmea_ids[0]}")
    assert get_fmea_res.status_code == 404
