def test_dashboard_stats_endpoint(client):
    # Setup some test data
    p = client.post("/api/v1/programs", json={
        "code": "P-DASH", "name": "Dashboard Vehicle", "platform": "EV", "lead_engineer": "Eng", "quality_manager": "QM"
    }).json()
    pt = client.post("/api/v1/parts", json={
        "program_id": p["id"], "part_number": "PT-DASH-01", "name": "Primary Weatherstrip",
        "subsystem": "Primary Body Seal", "category": "Elastomer", "supplier": "Cooper", "material": "EPDM"
    }).json()
    client.post("/api/v1/dfmea", json={
        "part_id": pt["id"], "fmea_code": "DFMEA-DASH-01", "item_function": "Seal",
        "failure_mode": "Leak", "failure_effect": "Wet", "severity": 9, "cause_mechanism": "Tear",
        "occurrence": 8, "prevention_control": "CAD", "detection_control": "Rain", "detection": 5
    })
    dvp = client.post("/api/v1/dvpr", json={
        "program_id": p["id"], "part_id": pt["id"], "plan_code": "DVP-DASH-01",
        "test_phase": "DV-A", "test_name": "Rain Test", "test_standard": "ISO", "acceptance_criteria": "No leak",
        "test_facility": "Booth", "planned_start_date": "2026-10-01", "planned_end_date": "2026-10-15",
        "status": "In Progress", "responsible_engineer": "Eng"
    }).json()
    client.post("/api/v1/tests", json={
        "dvpr_id": dvp["id"], "run_number": "RUN-DASH-01", "sample_id": "SMP-01", "test_date": "2026-10-10",
        "test_facility": "Booth", "operator": "Op", "result": "Pass"
    })
    client.post("/api/v1/issues", json={
        "issue_code": "ISS-DASH-01", "program_id": p["id"], "part_id": pt["id"],
        "title": "Minor clip loose", "severity": "S3-Minor", "status": "New", "description": "Clip loose",
        "occurrence_phase": "DV", "assignee": "Eng", "reporter": "Op", "due_date": "2026-11-01"
    })

    res = client.get("/api/v1/dashboard/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_programs"] >= 1
    assert stats["total_parts"] >= 1
    assert stats["total_dfmeas"] >= 1
    assert stats["total_dvprs"] >= 1
    assert stats["total_test_runs"] >= 1
    assert stats["total_issues"] >= 1
    assert stats["dfmea_high_ap_count"] >= 1
    assert stats["test_run_pass_rate_pct"] == 100.0
    assert "Primary Body Seal" in [s["subsystem"] for s in stats["subsystem_health"]]
