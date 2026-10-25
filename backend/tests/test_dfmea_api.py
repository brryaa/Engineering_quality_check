def test_create_dfmea_auto_rpn_ap(client):
    # Program & Part setup
    p_res = client.post("/api/v1/programs", json={
        "code": "P-FMEA-P",
        "name": "FMEA Vehicle",
        "platform": "EV",
        "lead_engineer": "Eng",
        "quality_manager": "QM"
    })
    prog_id = p_res.json()["id"]

    pt_res = client.post("/api/v1/parts", json={
        "program_id": prog_id,
        "part_number": "PT-FMEA-01",
        "name": "Tailgate Spindle Strut",
        "subsystem": "Power Tailgate System",
        "category": "Electro-Mechanical",
        "supplier": "Stabilus",
        "material": "Aluminum/Steel",
        "revision": "Rev A.0",
        "weight_kg": 3.4,
        "safety_critical": True
    })
    part_id = pt_res.json()["id"]

    # Create DFMEA with Severity 9, Occurrence 8, Detection 5 -> AP should be High, RPN = 9*8*5 = 360
    fmea_payload = {
        "part_id": part_id,
        "fmea_code": "DFMEA-SPINDLE-001",
        "item_function": "Open and hold tailgate in all thermal conditions",
        "failure_mode": "Spindle strut stall and thermal lockout at extreme cold -40C",
        "failure_effect": "Tailgate drops down, potential passenger injury",
        "severity": 9,
        "cause_mechanism": "Internal lubricant freeze viscosity increase",
        "occurrence": 8,
        "prevention_control": "Low temp grease spec G-441",
        "detection_control": "Chamber dyno cycle test",
        "detection": 5,
        "recommended_action": "Switch to synthetic aerospace low temp lubricant"
    }

    res = client.post("/api/v1/dfmea", json=fmea_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["rpn"] == 360
    assert data["action_priority"] == "High"
    assert data["part_number"] == "PT-FMEA-01"

    # Update DFMEA with post-action scores
    update_payload = {
        "post_severity": 9,
        "post_occurrence": 2,
        "post_detection": 2,
        "action_status": "Verified"
    }
    up_res = client.put(f"/api/v1/dfmea/{data['id']}", json=update_payload)
    assert up_res.status_code == 200
    up_data = up_res.json()
    assert up_data["post_rpn"] == 36  # 9 * 2 * 2
    assert up_data["action_status"] == "Verified"
