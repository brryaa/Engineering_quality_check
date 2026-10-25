def test_create_change_and_approval_workflow(client):
    p = client.post("/api/v1/programs", json={
        "code": "P-CHG-P", "name": "Change Program", "platform": "EV", "lead_engineer": "Eng", "quality_manager": "QM"
    }).json()
    pt = client.post("/api/v1/parts", json={
        "program_id": p["id"], "part_number": "PT-CHG-01", "name": "Check Link Arm",
        "subsystem": "Door Hinge & Check Link", "category": "Mechanical", "supplier": "Brose", "material": "Steel",
        "revision": "Rev A.0"
    }).json()

    ecr_payload = {
        "change_code": "ECR-2026-CHG01",
        "program_id": p["id"],
        "part_id": pt["id"],
        "title": "Upgrade check link nylon overmold to POM-GF30",
        "change_type": "Material-Change",
        "reason": "Eliminate detent force degradation after 50k cycles",
        "pre_change_rev": "Rev A.0",
        "post_change_rev": "Rev B.0",
        "cost_impact_rmb": 3.5,
        "weight_impact_kg": -0.02,
        "tooling_lead_weeks": 4,
        "requires_homologation": False,
        "requires_dvp_retest": True,
        "approval_status": "Draft",
        "initiator": "Frank Becker"
    }
    res = client.post("/api/v1/changes", json=ecr_payload)
    assert res.status_code == 201
    ecr_data = res.json()
    assert ecr_data["approval_status"] == "Draft"
    assert ecr_data["approval_date"] is None

    # Step 1: Approve change
    app_res = client.put(f"/api/v1/changes/{ecr_data['id']}", json={
        "approval_status": "Approved",
        "approver": "Chief Engineer"
    })
    assert app_res.status_code == 200
    app_data = app_res.json()
    assert app_data["approval_status"] == "Approved"
    assert app_data["approval_date"] is not None

    # Step 2: Implement change -> should automatically update Part's revision to Rev B.0!
    imp_res = client.put(f"/api/v1/changes/{ecr_data['id']}", json={
        "approval_status": "Implemented"
    })
    assert imp_res.status_code == 200

    part_updated = client.get(f"/api/v1/parts/{pt['id']}").json()
    assert part_updated["revision"] == "Rev B.0"
